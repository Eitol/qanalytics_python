"""
Test
"""
from datetime import datetime

from qanalytics_python.qanalytics import QAnalytics, QAnalyticsRespCode

DEFAULT_TEST_USER = "WS_test"
DEFAULT_TEST_PASSWORD = "$$WS17"


def test_send_wm_ins_reporte_punto_a_punto():
    """
    Thest the happy path
    :return:
    """
    qa_client = QAnalytics(DEFAULT_TEST_USER, DEFAULT_TEST_PASSWORD)
    data = {
        "ID_REG": "test",
        "LATITUD": -32.1212,
        "LONGITUD": -72.551,
        "VELOCIDAD": 0,
        "SENTIDO": 0,
        "FH_DATO": datetime.now(),
        "PLACA": "TEST",
        "CANT_SATELITES": 1,
        "HDOP": 1,
        "TEMP1": 999,
        "TEMP2": 999,
        "TEMP3": 999,
        "SENSORA_1": -1,
        "AP": -1,
        "IGNICION": -1,
        "PANICO": -1,
        "SENSORD_1": -1,
        "TRANS": "TEST",
    }
    resp = qa_client.send_request(data, "/gps_test/service.asmx", "WM_INS_REPORTE_PUNTO_A_PUNTO")
    assert resp.code == QAnalyticsRespCode.CORRECTO
    assert resp.http_code == 200
