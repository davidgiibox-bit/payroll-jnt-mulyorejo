import os
import json

import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]


class GoogleSheetsBelumDikonfigurasi(Exception):
    """Dilempar kalau kredensial/ID spreadsheet belum di-set di environment."""


def _ambil_kredensial():
    isi_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_JSON_CONTENT")
    path_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_JSON")

    if isi_json:
        info = json.loads(isi_json)
        return Credentials.from_service_account_info(info, scopes=SCOPES)
    if path_json:
        return Credentials.from_service_account_file(path_json, scopes=SCOPES)

    raise GoogleSheetsBelumDikonfigurasi(
        "Kredensial Google Sheets belum diatur. Set env var GOOGLE_SHEETS_CREDENTIALS_JSON "
        "(path file) atau GOOGLE_SHEETS_CREDENTIALS_JSON_CONTENT (isi JSON langsung)."
    )


def _ambil_spreadsheet_id():
    spreadsheet_id = os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID")
    if not spreadsheet_id:
        raise GoogleSheetsBelumDikonfigurasi(
            "GOOGLE_SHEETS_SPREADSHEET_ID belum diatur di environment."
        )
    return spreadsheet_id


def buka_spreadsheet_absensi():
    """Buka spreadsheet 'Absensi Internal J&T Express'. Melempar
    GoogleSheetsBelumDikonfigurasi kalau env var belum diatur."""
    kredensial = _ambil_kredensial()
    client = gspread.authorize(kredensial)
    return client.open_by_key(_ambil_spreadsheet_id())


def ambil_semua_baris(worksheet):
    """Ambil semua baris sebagai list of dict (baris pertama dipakai sebagai header)."""
    return worksheet.get_all_records()
