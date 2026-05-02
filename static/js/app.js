const accessTokenKey = "wms_access_token";
const refreshTokenKey = "wms_refresh_token";

const loginCard = document.getElementById("login-card");
const dashboard = document.getElementById("dashboard");
const productTable = document.getElementById("product-table");
const productCardList = document.getElementById("product-card-list");
const recordList = document.getElementById("record-list");
const homeRecordList = document.getElementById("home-record-list");
const memberTable = document.getElementById("member-table");
const auditLogTable = document.getElementById("audit-log-table");
const memberCreateCard = document.getElementById("member-create-card");
const memberMaxCount = document.getElementById("member-max-count");
const memberCurrentCount = document.getElementById("member-current-count");
const productSelect = document.getElementById("record-product");
const warningProductSelect = document.getElementById("warning-product");
const productForm = document.getElementById("product-form");
const productFormTitle = document.getElementById("product-form-title");
const productSubmitBtn = document.getElementById("product-submit-btn");
const productCancelBtn = document.getElementById("product-cancel-btn");
const productImageInput = document.getElementById("product-image");
const productImagePreview = document.getElementById("product-image-preview");
const recordSearchInput = document.getElementById("record-search");
const exportStockInBtn = document.getElementById("export-stockin-btn");
const exportStockOutBtn = document.getElementById("export-stockout-btn");
const navButtons = document.querySelectorAll(".nav-btn");
const pagePanels = document.querySelectorAll(".page-panel");
const featureCards = document.querySelectorAll("[data-page-target]");
const refreshButtons = document.querySelectorAll(".refresh-page-btn");
const currentTimeLabel = document.getElementById("current-time");

let currentRecordSearch = "";
let currentPage = "home";
let latestAnalytics = null;
let currentProfile = null;
const chartInstances = {};

function formatNow(date) {
    const pad = (value) => String(value).padStart(2, "0");
    const year = date.getFullYear();
    const month = pad(date.getMonth() + 1);
    const day = pad(date.getDate());
    const hours = pad(date.getHours());
    const minutes = pad(date.getMinutes());
    const seconds = pad(date.getSeconds());
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

function startClock() {
    if (!currentTimeLabel) return;
    const update = () => {
        currentTimeLabel.textContent = formatNow(new Date());
    };
    update();
    window.setInterval(update, 1000);
    document.addEventListener("visibilitychange", () => {
        if (!document.hidden) update();
    });
}

function getToken() {
    return localStorage.getItem(accessTokenKey);
}

function setTokens(payload) {
    localStorage.setItem(accessTokenKey, payload.access);
    localStorage.setItem(refreshTokenKey, payload.refresh);
}

function clearTokens() {
    localStorage.removeItem(accessTokenKey);
    localStorage.removeItem(refreshTokenKey);
}

function handleForcedLogout(message) {
    clearTokens();
    window.applyWatermark("");
    setAuthState(false);
    alert(message || "账号已在其他设备登录，请重新登录。");
}

async function request(url, options = {}) {
    const headers = options.headers || {};
    if (getToken()) {
        headers.Authorization = `Bearer ${getToken()}`;
    }
    if (!(options.body instanceof FormData)) {
        headers["Content-Type"] = "application/json";
    }

    const response = await fetch(url, { ...options, headers });
    if (response.status === 401) {
        let errorData = {};
        try {
            errorData = await response.clone().json();
        } catch (e) {
            errorData = {};
        }
        const detail = errorData.detail || "";
        if (detail.includes("其他设备")) {
            handleForcedLogout(detail);
            throw new Error(detail);
        }
        clearTokens();
        setAuthState(false);
        throw new Error("登录已过期，请重新登录。");
    }
    let data = {};
    let rawText = "";
    try {
        data = await response.clone().json();
    } catch (e) {
        data = {};
        try {
            rawText = await response.text();
        } catch (e2) {
            rawText = "";
        }
    }
    if (!response.ok) {
        const fallbackMessage = rawText
            ? rawText.slice(0, 300)
            : `请求失败(${response.status})`;
        throw new Error(data.detail || JSON.stringify(data) || fallbackMessage);
    }
    return data;
}

async function downloadPdf(url, filename) {
    const response = await fetch(url, {
        headers: {
            Authorization: `Bearer ${getToken()}`,
        },
    });
    if (response.status === 401) {
        handleForcedLogout("登录已过期，请重新登录。");
        return;
    }
    if (!response.ok) {
        const message = await response.text();
        throw new Error(message || "导出失败。");
    }
    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(objectUrl);
}

function setAuthState(isAuthenticated) {
    loginCard.classList.toggle("hidden", isAuthenticated);
    dashboard.classList.toggle("hidden", !isAuthenticated);
}

function switchPage(pageName) {
    currentPage = pageName;
    pagePanels.forEach((panel) => {
        panel.classList.toggle("hidden", panel.dataset.page !== pageName);
        panel.classList.toggle("active", panel.dataset.page === pageName);
    });
    navButtons.forEach((button) => {
        button.classList.toggle("active", button.dataset.page === pageName);
    });
    if (pageName === "analytics" && latestAnalytics) {
        window.requestAnimationFrame(() => {
            renderCharts(latestAnalytics);
        });
    }
}

function fillProductOptions(products) {
    const productOptions = products
        .map((item) => `<option value="${item.id}">${item.name} (${item.sku})</option>`)
        .join("");
    const inventoryOptions = products
        .map((item) => `<option value="${item.inventory_id}">${item.name} (${item.sku})</option>`)
        .join("");
    productSelect.innerHTML = productOptions;
    warningProductSelect.innerHTML = inventoryOptions;
}

function resetProductForm() {
    productForm.reset();
    document.getElementById("product-id").value = "";
    productFormTitle.textContent = "添加商品";
    productSubmitBtn.textContent = "保存商品";
    productCancelBtn.classList.add("hidden");
    productImagePreview.src = "";
    productImagePreview.classList.add("hidden");
}

function renderProducts(products) {
    productTable.innerHTML = products
        .map(
            (item) => `
            <tr class="${item.is_low_stock ? "low-stock-row" : ""}">
                <td>${item.image_url ? `<img src="${item.image_url}" alt="${item.name}" class="product-thumb">` : '<div class="product-thumb placeholder">无图</div>'}</td>
                <td>${item.name}</td>
                <td>${item.sku}</td>
                <td>${item.category || "未分类"}</td>
                <td>${item.price}</td>
                <td class="${item.is_low_stock ? "low-stock-text" : ""}">${item.quantity ?? 0}</td>
                <td class="${item.is_low_stock ? "low-stock-text" : ""}">${item.warning_level ?? 0}${item.is_low_stock ? " (预警)" : ""}</td>
                <td>
                    <div class="action-buttons">
                        <button class="edit-btn" onclick="editProduct(${item.id})">修改</button>
                        <button class="danger-btn" onclick="deleteProduct(${item.id}, '${item.name.replace(/'/g, "\\'")}')">删除</button>
                    </div>
                </td>
            </tr>
        `
        )
        .join("");

    productCardList.innerHTML = products
        .map(
            (item) => `
            <article class="product-card ${item.is_low_stock ? "low-stock-row" : ""}">
                <div class="product-card-header">
                    <div>
                        ${item.image_url ? `<img src="${item.image_url}" alt="${item.name}" class="product-card-image">` : '<div class="product-card-image placeholder">暂无图片</div>'}
                        <strong>${item.name}</strong>
                        <div class="hint">SKU：${item.sku}</div>
                    </div>
                    <span class="${item.is_low_stock ? "low-stock-badge" : "stock-badge"}">
                        ${item.is_low_stock ? "低库存" : "正常"}
                    </span>
                </div>
                <div class="product-card-grid">
                    <div><span>分类</span><strong>${item.category || "未分类"}</strong></div>
                    <div><span>单价</span><strong>${item.price}</strong></div>
                    <div><span>库存</span><strong class="${item.is_low_stock ? "low-stock-text" : ""}">${item.quantity ?? 0}</strong></div>
                    <div><span>预警值</span><strong class="${item.is_low_stock ? "low-stock-text" : ""}">${item.warning_level ?? 0}</strong></div>
                </div>
                <div class="action-buttons product-card-actions">
                    <button class="edit-btn" onclick="editProduct(${item.id})">修改</button>
                    <button class="danger-btn" onclick="deleteProduct(${item.id}, '${item.name.replace(/'/g, "\\'")}')">删除</button>
                </div>
            </article>
        `
        )
        .join("");

    fillProductOptions(products);
}

async function editProduct(id) {
    try {
        const product = await request(`/api/products/${id}/`);
        document.getElementById("product-id").value = product.id;
        productForm.elements.name.value = product.name;
        productForm.elements.sku.value = product.sku;
        productForm.elements.category.value = product.category || "";
        productForm.elements.price.value = product.price;
        if (product.image_url) {
            productImagePreview.src = product.image_url;
            productImagePreview.classList.remove("hidden");
        } else {
            productImagePreview.src = "";
            productImagePreview.classList.add("hidden");
        }
        productFormTitle.textContent = "更新商品信息";
        productSubmitBtn.textContent = "保存修改";
        productCancelBtn.classList.remove("hidden");
        productForm.scrollIntoView({ behavior: "smooth", block: "center" });
    } catch (error) {
        alert(error.message);
    }
}

async function deleteProduct(id, name) {
    if (!confirm(`确认删除商品“${name}”吗？相关库存和出入库记录也会一起删除。`)) {
        return;
    }
    try {
        await request(`/api/products/${id}/`, {
            method: "DELETE",
        });
        await refreshDashboard();
    } catch (error) {
        alert(error.message);
    }
}

function renderRecords(stockin, stockout) {
    const merged = [
        ...stockin.map((item) => ({ ...item, type: "入库", endpoint: "stockin" })),
        ...stockout.map((item) => ({ ...item, type: "出库", endpoint: "stockout" })),
    ]
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        .slice(0, 8);

    recordList.innerHTML = merged
        .map(
            (item) => `
            <li>
                <div class="record-meta">
                    <strong>${item.type}</strong> ${item.product_name} × ${item.quantity}
                    <div>${new Date(item.created_at).toLocaleString()} / ${item.operator || "-"}</div>
                </div>
                <button class="danger-btn" onclick="deleteRecord('${item.endpoint}', ${item.id})">删除</button>
            </li>
        `
        )
        .join("");

    homeRecordList.innerHTML = merged
        .slice(0, 4)
        .map(
            (item) => `
            <li>
                <div class="record-meta">
                    <strong>${item.type}</strong> ${item.product_name} × ${item.quantity}
                    <div>${new Date(item.created_at).toLocaleString()} / 剩余库存 ${item.remaining_inventory ?? "-"}</div>
                </div>
            </li>
        `
        )
        .join("");

    document.getElementById("record-count").textContent = merged.length;
}

async function deleteRecord(endpoint, id) {
    if (!confirm("确认删除这条记录吗？删除后库存会自动回滚。")) {
        return;
    }
    try {
        await request(`/api/records/${endpoint}/${id}/`, {
            method: "DELETE",
        });
        await refreshDashboard();
    } catch (error) {
        alert(error.message);
    }
}

function renderCharts(analytics) {
    if (typeof echarts === "undefined") {
        return;
    }

    latestAnalytics = analytics;

    const trendDays = analytics.trend_comparison.map((item) => item.day);
    const stockinSeries = analytics.trend_comparison.map((item) => item.stockin);
    const stockoutSeries = analytics.trend_comparison.map((item) => item.stockout);
    const totalCategoryValue = analytics.category_share.reduce((sum, item) => sum + item.value, 0);

    const stockinElement = document.getElementById("stockin-chart");
    const stockoutElement = document.getElementById("stockout-chart");
    const shareElement = document.getElementById("share-chart");
    const topElement = document.getElementById("top-chart");

    if (!stockinElement.offsetWidth || !stockoutElement.offsetWidth || !shareElement.offsetWidth || !topElement.offsetWidth) {
        return;
    }

    chartInstances.stockin = echarts.getInstanceByDom(stockinElement) || echarts.init(stockinElement);
    chartInstances.stockout = echarts.getInstanceByDom(stockoutElement) || echarts.init(stockoutElement);
    chartInstances.share = echarts.getInstanceByDom(shareElement) || echarts.init(shareElement);
    chartInstances.top = echarts.getInstanceByDom(topElement) || echarts.init(topElement);

    chartInstances.stockin.setOption({
        tooltip: { trigger: "axis" },
        legend: { data: ["入库", "出库"] },
        grid: { left: 24, right: 20, top: 40, bottom: 24, containLabel: true },
        xAxis: { type: "category", boundaryGap: false, data: trendDays },
        yAxis: { type: "value", name: "数量" },
        series: [
            {
                name: "入库",
                type: "line",
                smooth: true,
                symbol: "circle",
                symbolSize: 8,
                areaStyle: { color: "rgba(37, 99, 235, 0.12)" },
                lineStyle: { width: 3, color: "#2563eb" },
                itemStyle: { color: "#2563eb" },
                data: stockinSeries,
            },
            {
                name: "出库",
                type: "line",
                smooth: true,
                symbol: "circle",
                symbolSize: 8,
                areaStyle: { color: "rgba(220, 38, 38, 0.10)" },
                lineStyle: { width: 3, color: "#dc2626" },
                itemStyle: { color: "#dc2626" },
                data: stockoutSeries,
            },
        ],
    });

    chartInstances.stockout.setOption({
        tooltip: { trigger: "axis" },
        grid: { left: 24, right: 20, top: 24, bottom: 24, containLabel: true },
        xAxis: {
            type: "category",
            data: analytics.inventory_status.map((item) => item.name),
            axisLabel: { interval: 0, rotate: analytics.inventory_status.length > 4 ? 20 : 0 },
        },
        yAxis: { type: "value", name: "库存" },
        series: [
            {
                type: "line",
                smooth: true,
                name: "当前库存",
                data: analytics.inventory_status.map((item) => item.quantity),
                lineStyle: { width: 3, color: "#0f766e" },
                itemStyle: { color: "#0f766e" },
            },
            {
                type: "line",
                smooth: true,
                name: "预警值",
                data: analytics.inventory_status.map((item) => item.warning_level),
                lineStyle: { width: 2, type: "dashed", color: "#f59e0b" },
                itemStyle: { color: "#f59e0b" },
            },
        ],
        legend: { data: ["当前库存", "预警值"] },
    });

    chartInstances.share.setOption({
        tooltip: { trigger: "item" },
        legend: { bottom: 0, type: "scroll" },
        graphic: [
            {
                type: "text",
                left: "center",
                top: "42%",
                style: {
                    text: `总库存\n${totalCategoryValue}`,
                    textAlign: "center",
                    fill: "#1f2937",
                    fontSize: 16,
                    fontWeight: 700,
                },
            },
        ],
        series: [{
            type: "pie",
            radius: ["42%", "68%"],
            center: ["50%", "42%"],
            avoidLabelOverlap: true,
            label: {
                formatter: "{b}\n{d}%",
            },
            data: analytics.category_share,
        }],
    });

    chartInstances.top.setOption({
        tooltip: { trigger: "axis" },
        grid: { left: 24, right: 20, top: 24, bottom: 36, containLabel: true },
        xAxis: { type: "category", data: analytics.top_products.map((item) => item.name) },
        yAxis: { type: "value" },
        series: [{
            type: "bar",
            barWidth: 28,
            itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: "#60a5fa" },
                    { offset: 1, color: "#2563eb" },
                ]),
                borderRadius: [8, 8, 0, 0],
            },
            data: analytics.top_products.map((item) => item.value),
        }],
    });

    Object.values(chartInstances).forEach((chart) => chart.resize());
}

async function refreshDashboard() {
    const recordQuery = currentRecordSearch ? `?search=${encodeURIComponent(currentRecordSearch)}` : "";
    const requests = [
        request("/api/auth/me/"),
        request("/api/products/"),
        request(`/api/records/stockin/${recordQuery}`),
        request(`/api/records/stockout/${recordQuery}`),
        request("/api/analytics/"),
    ];

    if (currentPage === "accounts") {
        requests.push(request("/api/auth/team/subaccounts/"));
        requests.push(request("/api/auth/audit-logs/"));
    }

    const results = await Promise.allSettled(requests);

    const [profile, products, stockin, stockout, analyticsResult] = results;

    if (profile.status !== "fulfilled" || products.status !== "fulfilled" || stockin.status !== "fulfilled" || stockout.status !== "fulfilled") {
        const firstError = [profile, products, stockin, stockout].find((item) => item.status === "rejected");
        throw firstError.reason;
    }

    const analytics = analyticsResult.status === "fulfilled"
        ? analyticsResult.value
        : {
            trend_comparison: [],
            category_share: [],
            top_products: [],
            inventory_status: [],
            summary: {
                product_count: products.value.length,
                inventory_total: products.value.reduce((sum, item) => sum + (item.quantity || 0), 0),
                low_stock_count: products.value.filter((item) => item.is_low_stock).length,
            },
        };

    currentProfile = profile.value;
    document.getElementById("current-user").textContent = currentProfile.user.username;
    document.getElementById("current-team").textContent = `${currentProfile.team.name} (${currentProfile.team.code})`;
    document.getElementById("product-count").textContent = analytics.summary.product_count;
    document.getElementById("inventory-total").textContent = analytics.summary.inventory_total;
    document.getElementById("low-stock-count").textContent = analytics.summary.low_stock_count;

    renderProducts(products.value);
    renderRecords(stockin.value, stockout.value);
    
    if (currentPage === "analytics") {
        renderCharts(analytics);
    } else if (currentPage === "accounts") {
        const members = results[5].status === "fulfilled" ? results[5].value.members : [];
        const logs = results[6].status === "fulfilled" ? results[6].value : [];
        renderAccounts(members, logs);
    } else {
        latestAnalytics = analytics;
    }
    window.applyWatermark(profile.value.user.username);
}

function renderAccounts(members, logs) {
    const isAdmin = Boolean(currentProfile && currentProfile.is_team_admin);
    if (memberCreateCard) {
        memberCreateCard.classList.toggle("hidden", !isAdmin);
    }
    if (memberMaxCount && currentProfile && currentProfile.team) {
        memberMaxCount.textContent = currentProfile.team.max_subaccounts ?? "-";
    }
    if (memberCurrentCount && currentProfile && currentProfile.team) {
        memberCurrentCount.textContent = currentProfile.team.current_subaccounts ?? "-";
    }

    memberTable.innerHTML = members.map(m => `
        <tr>
            <td>${m.username}</td>
            <td>${m.role === "ADMIN" ? '<span class="badge danger">管理员</span>' : '<span class="badge info">成员</span>'}</td>
            <td>${new Date(m.date_joined).toLocaleString()}</td>
            <td>
                ${isAdmin && m.role !== "ADMIN" && currentProfile && m.id !== currentProfile.user.id
                    ? `<button class="danger-btn" onclick="deleteMember(${m.id}, '${m.username.replace(/'/g, "\\'")}')">删除</button>`
                    : "-"}
            </td>
        </tr>
    `).join("");

    auditLogTable.innerHTML = logs.map(log => `
        <tr>
            <td class="time-cell">${new Date(log.created_at).toLocaleString()}</td>
            <td><strong>${log.username}</strong></td>
            <td><span class="badge ${getLogBadgeClass(log.action)}">${log.action_display}</span></td>
            <td>${log.resource}</td>
            <td class="desc-cell">${log.description}</td>
        </tr>
    `).join("");
}

function getLogBadgeClass(action) {
    if (action === 'DELETE') return 'danger';
    if (action === 'CREATE') return 'success';
    if (action === 'UPDATE') return 'warning';
    if (action === 'LOGIN') return 'info';
    return '';
}

async function deleteMember(userId, username) {
    if (!confirm(`确认删除账号“${username}”吗？`)) {
        return;
    }
    try {
        await request("/api/auth/team/subaccounts/", {
            method: "DELETE",
            body: JSON.stringify({ user_id: userId }),
        });
        await refreshDashboard();
    } catch (error) {
        alert(error.message);
    }
}

window.deleteMember = deleteMember;

const authTabs = document.querySelectorAll(".auth-tab");
const loginPanel = document.getElementById("login-panel");
const registerPanel = document.getElementById("register-panel");

authTabs.forEach(tab => {
    tab.addEventListener("click", () => {
        authTabs.forEach(t => t.classList.remove("active"));
        tab.classList.add("active");
        if (tab.dataset.tab === "login") {
            loginPanel.classList.remove("hidden");
            registerPanel.classList.add("hidden");
        } else {
            loginPanel.classList.add("hidden");
            registerPanel.classList.remove("hidden");
        }
    });
});

document.getElementById("register-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const team_name = document.getElementById("reg-team-name").value;
    const team_code = document.getElementById("reg-team-code").value;
    const username = document.getElementById("reg-username").value;
    const password = document.getElementById("reg-password").value;

    try {
        await request("/api/auth/register/", {
            method: "POST",
            body: JSON.stringify({ team_name, team_code, username, password }),
        });
        alert("团队创建成功！请使用刚才的信息登录。");
        authTabs[0].click();
        document.getElementById("login-team-code").value = team_code;
        document.getElementById("username").value = username;
    } catch (error) {
        alert("注册失败：" + error.message);
    }
});

document.getElementById("login-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const teamCodeInput = document.getElementById("login-team-code");
    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");
    
    const team_code = teamCodeInput ? teamCodeInput.value : "";
    const username = usernameInput ? usernameInput.value : "";
    const password = passwordInput ? passwordInput.value : "";

    try {
        const payload = await request("/api/auth/login/", {
            method: "POST",
            body: JSON.stringify({
                "team_code": team_code,
                "username": username,
                "password": password
            }),
        });
        setTokens(payload);
        setAuthState(true);
        await refreshDashboard();
    } catch (error) {
        alert(error.message);
    }
});

document.getElementById("member-create-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const username = document.getElementById("member-username").value;
    const password = document.getElementById("member-password").value;
    try {
        await request("/api/auth/team/subaccounts/", {
            method: "POST",
            body: JSON.stringify({ username, password }),
        });
        event.target.reset();
        await refreshDashboard();
    } catch (error) {
        alert(error.message);
    }
});

productForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(event.target);
    const productId = formData.get("product_id");
    formData.delete("product_id");
    if (!formData.get("image") || !formData.get("image").name) {
        formData.delete("image");
    }
    try {
        await request(productId ? `/api/products/${productId}/` : "/api/products/", {
            method: productId ? "PATCH" : "POST",
            body: formData,
        });
        resetProductForm();
        await refreshDashboard();
    } catch (error) {
        alert(error.message);
    }
});

productCancelBtn.addEventListener("click", () => {
    resetProductForm();
});

productImageInput.addEventListener("change", () => {
    const file = productImageInput.files[0];
    if (!file) {
        productImagePreview.src = "";
        productImagePreview.classList.add("hidden");
        return;
    }
    productImagePreview.src = URL.createObjectURL(file);
    productImagePreview.classList.remove("hidden");
});

navButtons.forEach((button) => {
    button.addEventListener("click", () => {
        switchPage(button.dataset.page);
    });
});

featureCards.forEach((card) => {
    card.addEventListener("click", () => {
        switchPage(card.dataset.pageTarget);
    });
});

refreshButtons.forEach((button) => {
    button.addEventListener("click", async () => {
        button.disabled = true;
        const originalText = button.textContent;
        button.textContent = "刷新中...";
        try {
            await refreshDashboard();
        } catch (error) {
            alert(error.message);
        } finally {
            button.textContent = originalText;
            button.disabled = false;
        }
    });
});

document.getElementById("record-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const endpoint = document.getElementById("record-type").value;
    const payload = {
        product: document.getElementById("record-product").value,
        quantity: Number(document.getElementById("record-quantity").value),
        note: document.getElementById("record-note").value,
    };
    try {
        await request(`/api/records/${endpoint}/`, {
            method: "POST",
            body: JSON.stringify(payload),
        });
        event.target.reset();
        await refreshDashboard();
    } catch (error) {
        alert(error.message);
    }
});

document.getElementById("warning-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const inventoryId = document.getElementById("warning-product").value;
    try {
        await request(`/api/inventory/${inventoryId}/`, {
            method: "PATCH",
            body: JSON.stringify({ warning_level: Number(document.getElementById("warning-level").value) }),
        });
        event.target.reset();
        await refreshDashboard();
    } catch (error) {
        alert(error.message);
    }
});

document.getElementById("logout-btn").addEventListener("click", () => {
    clearTokens();
    window.applyWatermark("");
    setAuthState(false);
});

recordSearchInput.addEventListener("input", async (event) => {
    currentRecordSearch = event.target.value.trim();
    try {
        await refreshDashboard();
    } catch (error) {
        alert(error.message);
    }
});

exportStockInBtn.addEventListener("click", async () => {
    const query = currentRecordSearch ? `?search=${encodeURIComponent(currentRecordSearch)}` : "";
    try {
        await downloadPdf(`/api/records/stockin/export/pdf/${query}`, "入库记录报表.pdf");
    } catch (error) {
        alert(error.message);
    }
});

exportStockOutBtn.addEventListener("click", async () => {
    const query = currentRecordSearch ? `?search=${encodeURIComponent(currentRecordSearch)}` : "";
    try {
        await downloadPdf(`/api/records/stockout/export/pdf/${query}`, "出库记录报表.pdf");
    } catch (error) {
        alert(error.message);
    }
});

window.addEventListener("load", async () => {
    startClock();
    if (!getToken()) {
        setAuthState(false);
        return;
    }
    try {
        resetProductForm();
        setAuthState(true);
        switchPage(currentPage);
        await refreshDashboard();
    } catch (error) {
        alert(error.message);
    }
});

window.addEventListener("resize", () => {
    Object.values(chartInstances).forEach((chart) => chart.resize());
});
