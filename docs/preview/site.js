(() => {
  const supportsClipboard = !!(navigator.clipboard && navigator.clipboard.writeText);
  const isRu = (document.documentElement.lang || "").toLowerCase().startsWith("ru");
  const labels = isRu
    ? { copy: "Копировать", copied: "Скопировано", failed: "Ошибка" }
    : { copy: "Copy", copied: "Copied", failed: "Failed" };

  /* --- Copy buttons on <pre data-copy> --- */
  const addCopyButtons = () => {
    const blocks = document.querySelectorAll("pre[data-copy]");
    for (const pre of blocks) {
      if (pre.querySelector("button.copy-btn")) continue;

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "btn btn-sm copy-btn";
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

      /* Position inside the terminal wrapper, not the pre */
      const terminal = pre.closest(".terminal");
      if (terminal) {
        terminal.style.position = "relative";
        terminal.appendChild(btn);
      } else {
        pre.style.position = "relative";
        pre.appendChild(btn);
      }
    }
  };

  /* --- Scroll-triggered reveal --- */
  const initReveal = () => {
    const sections = document.querySelectorAll(".reveal");
    if (!sections.length) return;

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      sections.forEach((s) => s.classList.add("visible"));
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );

    sections.forEach((s) => observer.observe(s));
  };

  /* --- Mobile hamburger menu --- */
  const initHamburger = () => {
    const btn = document.querySelector(".hamburger");
    const menu = document.querySelector(".mobile-menu");
    if (!btn || !menu) return;

    btn.addEventListener("click", () => {
      const open = btn.getAttribute("aria-expanded") === "true";
      btn.setAttribute("aria-expanded", String(!open));
      menu.hidden = open;
    });

    /* Close on link click */
    menu.querySelectorAll("a").forEach((a) => {
      a.addEventListener("click", () => {
        btn.setAttribute("aria-expanded", "false");
        menu.hidden = true;
      });
    });
  };

  /* --- Smooth anchor offset for sticky nav --- */
  const initSmoothScroll = () => {
    document.querySelectorAll('a[href^="#"]').forEach((a) => {
      a.addEventListener("click", (e) => {
        const id = a.getAttribute("href")?.slice(1);
        const target = id && document.getElementById(id);
        if (target) {
          e.preventDefault();
          const navH = document.querySelector(".nav")?.offsetHeight || 60;
          const top = target.getBoundingClientRect().top + window.scrollY - navH - 16;
          window.scrollTo({ top, behavior: "smooth" });
          history.replaceState(null, "", `#${id}`);
        }
      });
    });
  };

  /* --- Init --- */
  const boot = () => {
    addCopyButtons();
    initReveal();
    initHamburger();
    initSmoothScroll();
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }
})();
