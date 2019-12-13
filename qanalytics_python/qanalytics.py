"""
Cliente para QAnalytics:
https://www.qanalytics.cl
"""

import enum
import re
from datetime import datetime
from typing import Dict, Any, Pattern
import pytz
import requests

DEFAULT_TIMEZONE_STR = 'Chile/Continental'
QANALYTICS_HOST = "ww2.qanalytics.cl"
DEFAULT_PROTOCOL = "http"
DEFAULT_NAMESPACE = "tem"


class QAnalyticsRespCode(enum.Enum):
    """
    Represents a standard QAnalytics response
    """
    UNKNOWN = "UNKNOWN"
    ERROR_DE_SESION = "ERROR DE SESION"
    ERROR_DE_INSERCION = "ERROR INSERCION"
    CORRECTO = "CORRECTO"
    
    REQUEST_ERROR = "REQUEST_ERROR"


class QAnalyticsResp(object):
    """
    Respuesta de QAnalytics
    """
    
    def __init__(self, code: QAnalyticsRespCode, http_code: int, text: str):
        self.code: QAnalyticsRespCode = code
        self.http_code = http_code
        self.text = text


class QAnalytics(object):
    """
    QAnalytics api wrapper
    """
    
    def __init__(self, user: str, password: str, timezone_str: str = DEFAULT_TIMEZONE_STR):
        """
        
        :param user: The QAnalytics secret user.         i.e: 'WS_test'
        :param password: The QAnalytics secret password. i.e: '$$WS17'
        :param timezone_str: Your timezone.              i.e: 'Chile/Continental'
        """
        self.user = user
        self.password = password
        self.timezone = pytz.timezone(timezone_str)
        self.protocol = DEFAULT_PROTOCOL
        self.host = QANALYTICS_HOST
    
    def send_request(self, data: Dict, endpoint: str, method: str,
                     namespace: str = DEFAULT_NAMESPACE) -> QAnalyticsResp:
        """
        Send a request to QAnalytics api
        :param data: A dictionary that contains all the required fields with their values
                     i.e: { "ID_REG": "test", ... }
        :param endpoint: i.e: "/gps_test/service.asmx"
        :param method: i.e: "WM_INS_REPORTE_PUNTO_A_PUNTO"
        :param namespace: OPTIONAL: i.e: "tem"
        :return:
        """
        header = self.__build_http_header(self.host, method)
        body = self.__build_body_soap(namespace, method, data)
        r = requests.post(self.__build_url(self.protocol, self.host, endpoint), data=body, headers=header)
        rt = self.__extract_result_text(r.text, method)
        try:
            code = QAnalyticsRespCode[rt.replace(" ", "_")]
        except KeyError:
            code = QAnalyticsRespCode.REQUEST_ERROR
        return QAnalyticsResp(code, r.status_code, rt)
    
    @staticmethod
    def __build_url(protocol: str, host: str, endpoint: str) -> str:
        return f"""{protocol}://{host}{endpoint}"""
    
    @staticmethod
    def __build_success_response_regex(method: str) -> Pattern:
        a = f"<{method}Result>(?P<resp>[A-Za-z_0-9 ]+)</{method}Result>"
        return re.compile(a, re.MULTILINE | re.DOTALL)
    
    @staticmethod
    def __build_fail_response_regex() -> Pattern:
        a = f"<faultstring>(?P<resp>.+)</faultstring>"
        return re.compile(a, re.MULTILINE | re.DOTALL)
    
    @classmethod
    def __extract_result_text(cls, result_text: str, method: str, last: bool = False) -> str:
        if not last:
            rgx = cls.__build_success_response_regex(method)
        else:
            rgx = cls.__build_fail_response_regex()
        match = rgx.search(result_text)
        if match is None and not last:
            return cls.__extract_result_text(result_text, method, True)
        return match.groupdict()['resp']
    
    @staticmethod
    def __build_http_header(host: str, method: str) -> Dict[str, str]:
        if not method.startswith("/"):
            method = "/" + method
        return {
            "Accept-Encoding": "gzip,deflate",
            "Content-Type": "text/xml;charset=UTF-8",
            "SOAPAction": f"http://tempuri.org{method}",
            "Host": f"{host}",
            "Connection": "Keep-Alive",
            "User-Agent": "Apache-HttpClient/4.5.2 (Java/1.8.0_181)"
        }
    
    @staticmethod
    def __build_soap_body_header(user: str, password: str, ns: str = "tem") -> str:
        schema = "http://schemas.xmlsoap.org/soap/envelope/"
        return f"""<soapenv:Envelope xmlns:soapenv="{schema}" xmlns:{ns}="http://tempuri.org/">
        <soapenv:Header>
            <{ns}:Authentication>
                <!--Optional:-->
                <{ns}:Usuario>{user}</{ns}:Usuario>
                <!--Optional:-->
                <{ns}:Clave>{password}</{ns}:Clave>
            </{ns}:Authentication>
        </soapenv:Header>\n
        """
    
    def __build_body_soap(self, namespace: str, method: str, data_dict: Dict[str, Any]):
        header = self.__build_soap_body_header(self.user, self.password)
        body = header + f"<soapenv:Body>\n\t<{namespace}:{method}>\n"
        template = f"\t\t\t<{namespace}:$KEY$>$VALUE$</{namespace}:$KEY$>\n"
        for key, value in data_dict.items():
            if isinstance(value, datetime):
                value_str = self.timezone.localize(value).isoformat()
            else:
                value_str = str(value)
            body += template.replace("$KEY$", key.upper()).replace('$VALUE$', value_str)
        body += f"\t\t</{namespace}:{method}>\n\t</soapenv:Body>\n</soapenv:Envelope>"
        return body
