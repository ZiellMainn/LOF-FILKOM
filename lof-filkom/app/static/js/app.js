/* Perilaku halaman. Tidak ada inline script (CSP: script-src 'self'). */
(function () {
  "use strict";

  // Menu mobile
  var tombol = document.querySelector(".tombol-menu");
  var topbar = document.querySelector(".topbar");
  if (tombol && topbar) {
    tombol.addEventListener("click", function () {
      var buka = topbar.classList.toggle("buka");
      tombol.setAttribute("aria-expanded", buka ? "true" : "false");
    });
  }

  // Lebar bar rekap dari atribut data-lebar
  document.querySelectorAll("[data-lebar]").forEach(function (el) {
    var w = parseFloat(el.getAttribute("data-lebar")) || 0;
    window.requestAnimationFrame(function () { el.style.width = Math.max(0, Math.min(100, w)) + "%"; });
  });

  // Cegah kirim ganda + indikator proses pada form
  document.querySelectorAll("form[data-proses]").forEach(function (form) {
    form.addEventListener("submit", function () {
      var b = form.querySelector("button[type=submit]");
      if (b && !b.disabled) {
        b.disabled = true;
        b.textContent = b.getAttribute("data-proses") || "Memproses...";
      }
    });
  });

  // Pratinjau foto sebelum diunggah
  var input = document.getElementById("foto");
  var pratinjau = document.getElementById("pratinjau");
  if (input && pratinjau) {
    input.addEventListener("change", function () {
      var f = input.files && input.files[0];
      if (!f) { pratinjau.classList.remove("tampil"); return; }
      if (f.size > 3 * 1024 * 1024) {
        input.value = "";
        pratinjau.classList.remove("tampil");
        alert("Ukuran foto maksimal 3 MB.");
        return;
      }
      pratinjau.src = URL.createObjectURL(f);
      pratinjau.classList.add("tampil");
    });
  }

  // Status laporan diperbarui otomatis setiap 15 detik (FR-06)
  var live = document.querySelector("[data-status-url]");
  if (live) {
    var terakhir = live.getAttribute("data-status") + "|" + live.getAttribute("data-riwayat");
    setInterval(function () {
      if (document.hidden) { return; }
      fetch(live.getAttribute("data-status-url"), { credentials: "same-origin", headers: { Accept: "application/json" } })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (d) {
          if (d && (d.status + "|" + d.riwayat) !== terakhir) { window.location.reload(); }
        })
        .catch(function () {});
    }, 15000);
  }
})();
