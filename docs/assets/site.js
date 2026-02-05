(() => {
  const supportsClipboard = !!(navigator.clipboard && navigator.clipboard.writeText);
  const isRu = (document.documentElement.lang || "").toLowerCase().startsWith("ru");
  const labels = isRu
    ? { copy: "Копировать", copied: "Скопировано", failed: "Ошибка" }
    : { copy: "Copy", copied: "Copied", failed: "Failed" };

  const addCopyButtons = () => {
    const blocks = document.querySelectorAll("pre[data-copy]");
    for (const pre of blocks) {
      if (pre.querySelector("button.copy")) continue;

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "btn small copy";
      btn.textContent = labels.copy;

      const code = pre.querySelector("code");
      const getText = () => (code ? code.innerText : pre.innerText);

      if (!supportsClipboard) {
        btn.disabled = true;
        btn.title = "Clipboard API is not available in this browser.";
      } else {
        btn.addEventListener("click", async () => {
          try {
            await navigator.clipboard.writeText(getText());
            const prev = btn.textContent;
            btn.textContent = labels.copied;
            window.setTimeout(() => (btn.textContent = prev), 1200);
          } catch {
            const prev = btn.textContent;
            btn.textContent = labels.failed;
            window.setTimeout(() => (btn.textContent = prev), 1200);
          }
        });
      }

      pre.appendChild(btn);
    }
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", addCopyButtons, { once: true });
  } else {
    addCopyButtons();
  }
})();

