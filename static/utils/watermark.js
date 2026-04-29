(function () {
    function ensureLayer() {
        let layer = document.getElementById("watermark-layer");
        if (!layer) {
            layer = document.createElement("div");
            layer.id = "watermark-layer";
            layer.style.position = "fixed";
            layer.style.inset = "0";
            layer.style.pointerEvents = "none";
            layer.style.zIndex = "9999";
            document.body.appendChild(layer);
        }
        return layer;
    }

    window.applyWatermark = function applyWatermark(text) {
        const layer = ensureLayer();
        layer.innerHTML = "";
        if (!text) {
            return;
        }

        for (let row = 0; row < 5; row += 1) {
            for (let col = 0; col < 4; col += 1) {
                const mark = document.createElement("div");
                mark.textContent = `当前用户: ${text}禁止截屏`;
                mark.style.position = "absolute";
                mark.style.left = `${col * 25}%`;
                mark.style.top = `${row * 20}%`;
                mark.style.transform = "rotate(-25deg)";
                mark.style.color = "rgba(148, 163, 184, 0.18)";
                mark.style.fontSize = "24px";
                mark.style.fontWeight = "700";
                mark.style.whiteSpace = "nowrap";
                layer.appendChild(mark);
            }
        }
    };
})();
