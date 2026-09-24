import io

import openpyxl
from flask import send_file


def kirim_template_excel(nama_file, kolom, contoh_baris, daftar_jenis=None, judul_daftar_jenis="Daftar Jenis"):
    """Bangun file template .xlsx (sheet pertama = template untuk diisi, dibaca importer)
    dan kirim sebagai download. daftar_jenis (opsional) ditaruh di sheet kedua sebagai
    contekan nilai yang valid -- importer hanya membaca sheet pertama."""
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Template"
    sheet.append(kolom)
    sheet.append(contoh_baris)

    if daftar_jenis is not None:
        sheet_jenis = workbook.create_sheet(judul_daftar_jenis)
        sheet_jenis.append([judul_daftar_jenis])
        for nama in daftar_jenis:
            sheet_jenis.append([nama])

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=nama_file,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
