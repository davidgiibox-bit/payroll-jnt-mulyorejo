// Urutkan tabel dengan klik judul kolom (naik -> turun -> kembali ke urutan awal).
// Otomatis berlaku untuk semua <table> yang punya <thead>. Judul kolom kosong
// (checkbox / tombol aksi) dan baris pesan kosong (colspan) tidak ikut diurutkan.
(function () {
  function angka(teks) {
    var t = teks.replace(/\s+/g, '');
    if (!/^[-+]?(Rp)?-?[\d.,]+%?$/i.test(t)) return null;
    var negatif = t.indexOf('-') !== -1;
    t = t.replace(/[^\d.,]/g, '');
    if (t === '') return null;
    if (t.indexOf('.') !== -1 && t.indexOf(',') !== -1) t = t.replace(/\./g, '').replace(',', '.');
    else if (/^\d{1,3}(\.\d{3})+$/.test(t)) t = t.replace(/\./g, '');
    else t = t.replace(',', '.');
    var n = parseFloat(t);
    if (isNaN(n)) return null;
    return negatif ? -n : n;
  }

  function nilaiSel(sel) {
    var mentah = sel.dataset.sort !== undefined ? sel.dataset.sort : sel.textContent;
    return mentah.trim();
  }

  function bandingkan(a, b) {
    var na = angka(a), nb = angka(b);
    if (na !== null && nb !== null) return na - nb;
    if (a === '' && b !== '') return 1;
    if (b === '' && a !== '') return -1;
    return a.localeCompare(b, 'id', { numeric: true, sensitivity: 'base' });
  }

  function pasang(tabel) {
    var thead = tabel.tHead;
    var tbody = tabel.tBodies[0];
    if (!thead || !thead.rows.length || !tbody) return;
    var headerRow = thead.rows[0];
    var barisAsli = Array.prototype.slice.call(tbody.rows);
    var aktif = { kolom: -1, arah: 0 };

    Array.prototype.forEach.call(headerRow.cells, function (th, kolom) {
      if (th.textContent.trim() === '' || th.classList.contains('no-sort') || th.querySelector('input')) return;
      th.style.cursor = 'pointer';
      th.style.userSelect = 'none';
      th.title = 'Klik untuk mengurutkan';
      var panah = document.createElement('span');
      panah.className = 'text-muted ms-1 small';
      th.appendChild(panah);

      th.addEventListener('click', function () {
        aktif.arah = aktif.kolom === kolom ? (aktif.arah === 1 ? -1 : (aktif.arah === -1 ? 0 : 1)) : 1;
        aktif.kolom = kolom;

        Array.prototype.forEach.call(headerRow.cells, function (h) {
          var p = h.querySelector('span.small.ms-1');
          if (p) p.textContent = '';
        });
        panah.textContent = aktif.arah === 1 ? '▲' : (aktif.arah === -1 ? '▼' : '');

        var semua = Array.prototype.slice.call(tbody.rows);
        var data = semua.filter(function (tr) { return !tr.querySelector('td[colspan]'); });
        var lain = semua.filter(function (tr) { return tr.querySelector('td[colspan]'); });
        var urut;
        if (aktif.arah === 0) {
          urut = barisAsli.filter(function (tr) { return data.indexOf(tr) !== -1; });
        } else {
          var indeks = new Map();
          data.forEach(function (tr, i) { indeks.set(tr, i); });
          urut = data.slice().sort(function (r1, r2) {
            var c1 = r1.cells[kolom], c2 = r2.cells[kolom];
            var hasil = bandingkan(c1 ? nilaiSel(c1) : '', c2 ? nilaiSel(c2) : '');
            if (hasil === 0) return indeks.get(r1) - indeks.get(r2);
            return aktif.arah * hasil;
          });
        }
        urut.concat(lain).forEach(function (tr) { tbody.appendChild(tr); });
        tabel.dispatchEvent(new CustomEvent('tabel-diurutkan'));
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('table').forEach(pasang);
  });
})();
