(() => {
  const csrfToken = document
    .querySelector('meta[name="csrf-token"]')
    ?.getAttribute("content");

  const statusClasses = [
    "status-pending",
    "status-included",
    "status-excluded",
    "status-review"
  ];

  const applyStatusClass = (select, statusValue) => {
    select.classList.remove(...statusClasses);
    if (statusValue) {
      select.classList.add(`status-${statusValue}`);
    }
  };

  document.querySelectorAll(".js-status-select").forEach((select) => {
    applyStatusClass(select, select.value);

    select.addEventListener("change", async (event) => {
      const currentSelect = event.currentTarget;
      const feedback = currentSelect.parentElement.querySelector(".js-status-feedback");
      const previousStatus = currentSelect.dataset.originalStatus;

      applyStatusClass(currentSelect, currentSelect.value);
      currentSelect.disabled = true;
      feedback.textContent = "Guardando...";
      feedback.className = "status-feedback text-secondary js-status-feedback";

      try {
        const response = await fetch(currentSelect.dataset.url, {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-CSRFToken": csrfToken || "",
            "X-Requested-With": "XMLHttpRequest"
          },
          body: new URLSearchParams({
            status: currentSelect.value
          })
        });

        const data = await response.json();

        if (!response.ok || !data.ok) {
          throw new Error(data.error || "No se pudo actualizar el estado.");
        }

        currentSelect.dataset.originalStatus = currentSelect.value;
        feedback.textContent = "Guardado";
        feedback.className = "status-feedback text-success js-status-feedback";
      } catch (error) {
        currentSelect.value = previousStatus;
        applyStatusClass(currentSelect, previousStatus);
        feedback.textContent = "Error";
        feedback.className = "status-feedback text-danger js-status-feedback";
      } finally {
        currentSelect.disabled = false;
      }
    });
  });

  document.querySelectorAll(".js-table-scroll-body").forEach((scrollBody) => {
    const shell = scrollBody.closest(".article-table-shell");
    const scrollTop = scrollBody.parentElement.querySelector(".js-table-scroll-top");
    const scrollTopInner = scrollTop?.querySelector(".js-table-scroll-top-inner");
    const stickyHeader = scrollBody.parentElement.querySelector(".js-table-sticky-header");
    const originalHead = scrollBody.querySelector(".js-table-head-origin");
    const table = scrollBody.querySelector(".article-table");

    if (!shell || !scrollTop || !scrollTopInner || !stickyHeader || !originalHead || !table) {
      return;
    }

    const stickyHeaderTable = stickyHeader.querySelector("table");

    if (!stickyHeaderTable) {
      return;
    }

    const syncStickyLayout = () => {
      scrollTopInner.style.width = `${table.scrollWidth}px`;
      stickyHeaderTable.style.width = `${table.scrollWidth}px`;
      const stickyOffset = window.innerWidth <= 767.98 ? scrollTop.offsetHeight : 0;
      shell.style.setProperty("--article-header-offset", `${stickyOffset}px`);
    };

    const syncStickyVisibility = () => {
      const headRect = originalHead.getBoundingClientRect();
      const shellRect = shell.getBoundingClientRect();
      const stickyOffset = parseFloat(
        getComputedStyle(shell).getPropertyValue("--article-header-offset")
      ) || 0;
      const shouldShow =
        headRect.top <= stickyOffset &&
        shellRect.bottom > stickyOffset + originalHead.offsetHeight;

      stickyHeader.classList.toggle("is-visible", shouldShow);
    };

    const syncHorizontalScroll = (scrollLeft) => {
      scrollTop.scrollLeft = scrollLeft;
      stickyHeader.scrollLeft = scrollLeft;
    };

    let isSyncingTop = false;
    let isSyncingBody = false;
    let isSyncingHeader = false;

    scrollTop.addEventListener("scroll", () => {
      if (isSyncingTop) {
        isSyncingTop = false;
        return;
      }

      isSyncingBody = true;
      scrollBody.scrollLeft = scrollTop.scrollLeft;
      isSyncingHeader = true;
      stickyHeader.scrollLeft = scrollTop.scrollLeft;
    });

    scrollBody.addEventListener("scroll", () => {
      if (isSyncingBody) {
        isSyncingBody = false;
        return;
      }

      isSyncingTop = true;
      isSyncingHeader = true;
      syncHorizontalScroll(scrollBody.scrollLeft);
    });

    stickyHeader.addEventListener("scroll", () => {
      if (isSyncingHeader) {
        isSyncingHeader = false;
        return;
      }

      isSyncingTop = true;
      isSyncingBody = true;
      scrollTop.scrollLeft = stickyHeader.scrollLeft;
      scrollBody.scrollLeft = stickyHeader.scrollLeft;
    });

    syncStickyLayout();
    syncHorizontalScroll(scrollBody.scrollLeft);
    syncStickyVisibility();
    window.addEventListener("resize", syncStickyLayout);
    window.addEventListener("resize", syncStickyVisibility);
    window.addEventListener("scroll", syncStickyVisibility, { passive: true });
  });
})();
