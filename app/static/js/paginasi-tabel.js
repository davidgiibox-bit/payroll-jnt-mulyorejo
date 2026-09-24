// Pagination otomatis untuk semua <table> yang punya lebih dari 10 baris data.
// Pilihan baris per halaman: 10 / 25 / 50 / 100 (disimpan di browser, default 25).
// Bekerja bersama sort-tabel.js (sort -> kembali ke halaman 1) dan filter yang
// menyembunyikan baris lewat style.display (mis. pencarian di halaman Review).
(function () {
  var PILIHAN = [10, 25, 50, 100];
  var KUNCI = 'payroll_baris_per_halaman';

  var css = document.createElement('style');
  css.textContent = 'tr[data-hal-sembunyi]{display:none !important;}';
  document.head.appendChild(css);

  function bacaPerHalaman() {
    try {
      var v = parseInt(localStorage.getItem(KUNCI), 10);
      if (PILIHAN.indexOf(v) !== -1) return v;
    } catch (e) {}
    return 25;
  }

  function simpanPerHalaman(v) {
    try { localStorage.setItem(KUNCI, String(v)); } catch (e) {}
  }

  function daftarHalaman(sekarang, total) {
    var hasil = [], awal = Math.max(1, sekarang - 2), akhir = Math.min(total, sekarang + 2);
    if (awal > 1) { hasil.push(1); if (awal > 2) hasil.push('...'); }
    for (var i = awal; i <= akhir; i++) hasil.push(i);
    if (akhir < total) { if (akhir < total - 1) hasil.push('...'); hasil.push(total); }
    return hasil;
  }

  function pasang(tabel) {
    if (tabel.closest('table') !== tabel || !tabel.tBodies[0]) return;
    var tbody = tabel.tBodies[0];
    var state = { halaman: 1, perHalaman: bacaPerHalaman() };

    var bar = document.createElement('div');
    bar.className = 'd-flex justify-content-between align-items-center flex-wrap gap-2 px-2 py-2 border-top small';
    bar.style.display = 'none';
    var pembungkus = tabel.closest('.table-responsive') || tabel;
    pembungkus.insertAdjacentElement('afterend', bar);

    var terjadwal = false;
    function jadwalkan() {
      if (terjadwal) return;
      terjadwal = true;
      setTimeout(function () { terjadwal = false; render(); }, 0);
    }

    function render() {
      var semua = Array.prototype.filter.call(tbody.rows, function (tr) { return !tr.querySelector('td[colspan]'); });
      var terfilter = semua.filter(function (tr) { return tr.style.display !== 'none'; });
      var total = terfilter.length;
      semua.forEach(function (tr) { tr.removeAttribute('data-hal-sembunyi'); });

      if (total <= PILIHAN[0]) { bar.style.display = 'none'; return; }

      var totalHal = Math.max(1, Math.ceil(total / state.perHalaman));
      if (state.halaman > totalHal) state.halaman = totalHal;
      var mulai = (state.halaman - 1) * state.perHalaman;
      terfilter.forEach(function (tr, i) {
        if (i < mulai || i >= mulai + state.perHalaman) tr.setAttribute('data-hal-sembunyi', '');
      });

      bar.style.display = '';
      bar.innerHTML = '';

      var kiri = document.createElement('div');
      kiri.className = 'd-flex align-items-center gap-2';
      var label = document.createElement('label');
      label.className = 'mb-0';
      label.textContent = 'Baris per halaman';
      var pilih = document.createElement('select');
      pilih.className = 'form-select form-select-sm';
      pilih.style.width = 'auto';
      PILIHAN.forEach(function (n) {
        var o = document.createElement('option');
        o.value = n; o.textContent = n; o.selected = n === state.perHalaman;
        pilih.appendChild(o);
      });
      pilih.addEventListener('change', function () {
        state.perHalaman = parseInt(pilih.value, 10);
        state.halaman = 1;
        simpanPerHalaman(state.perHalaman);
        render();
      });
      var info = document.createElement('span');
      info.className = 'text-muted';
      info.textContent = 'Menampilkan ' + (mulai + 1) + '–' + Math.min(mulai + state.perHalaman, total) + ' dari ' + total;
      kiri.appendChild(label); kiri.appendChild(pilih); kiri.appendChild(info);

      var nav = document.createElement('div');
      nav.className = 'd-flex gap-1';
      function tombol(teks, halaman, nonaktif, aktif) {
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'btn btn-sm ' + (aktif ? 'btn-primary' : 'btn-outline-secondary');
        b.textContent = teks;
        b.disabled = !!nonaktif;
        if (!nonaktif && halaman) b.addEventListener('click', function () { state.halaman = halaman; render(); });
        return b;
      }
      nav.appendChild(tombol('‹', state.halaman - 1, state.halaman === 1));
      daftarHalaman(state.halaman, totalHal).forEach(function (h) {
        if (h === '...') nav.appendChild(tombol('…', null, true));
        else nav.appendChild(tombol(h, h, false, h === state.halaman));
      });
      nav.appendChild(tombol('›', state.halaman + 1, state.halaman === totalHal));

      bar.appendChild(kiri); bar.appendChild(nav);
    }

    new MutationObserver(jadwalkan).observe(tbody, {
      childList: true, subtree: true, attributes: true, attributeFilter: ['style']
    });
    tabel.addEventListener('tabel-diurutkan', function () { state.halaman = 1; jadwalkan(); });
    render();
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('table').forEach(pasang);
  });
})();
