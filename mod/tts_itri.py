# Ref: http://tts.itri.org.tw/development/web_service_api.php

# 工研院文字轉語音Web服務 http://tts.itri.org.tw/
# 所合成之語音資料不得再自行修改變造。
# 本服務有權要求會員於其應用網頁或系統適當位置處，進行標示「工研院文字轉語音試用服務產出之合成語音」。

import http.client
import xml.dom.minidom as mdom
import time

from . import passwd # do NOT commit passwd.py to GitHub !

def text2wav(saytext): # requiring saytext as string, return wav file as binray

    # ConvertAdvancedText
    payload = ("""<?xml version="1.0" encoding="UTF-8"?>
    <soap:Envelope
      xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
      xmlns:xsd="http://www.w3.org/2001/XMLSchema"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xmlns:ns1="http://tts.itri.org.tw/TTSService/ConvertAdvancedText"
      soap:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
      <soap:Body>
        <ns1:ConvertAdvancedText>
            <accountID xsi:type="xsd:string">"""+passwd.itri_acc+"""</accountID>
            <password xsi:type="xsd:string">"""+passwd.itri_pas+"""</password>
            <TTStext xsi:type="xsd:string">"""+saytext+"""</TTStext>
            <TTSSpeaker xsi:type="xsd:string">Angela</TTSSpeaker>
            <volume xsi:type="xsd:int">100</volume>
            <speed xsi:type="xsd:int">2</speed>
            <outType xsi:type="xsd:string">wav</outType>
            <PitchLevel xsi:type="xsd:string">3</PitchLevel>
            <PitchSign xsi:type="xsd:string">0</PitchSign>
            <PitchScale xsi:type="xsd:string">7</PitchScale>
        </ns1:ConvertAdvancedText>
      </soap:Body>
    </soap:Envelope>
    """).encode('utf-8')

    head = {'Content-Type':'text-xml; charset=utf-8',
        'SOAPAction':'http://tts.itri.org.tw/TTSService/ConvertAdvancedText'}

    conn = http.client.HTTPConnection('tts.itri.org.tw:80')

    try:
        conn.request("POST","/TTSService/Soap_1_3.php", payload, head)
        request = conn.getresponse().read().decode('utf-8')
        result = mdom.parseString(request).getElementsByTagName('Result')[0].firstChild.data
        convID = result.split('&')[2]
        print("[T2W] Got Convert ID: "+convID)
    except:
        convID = '0'
        return

    # GetConvertStatus
    payload = ("""<?xml version="1.0" encoding="UTF-8"?>
    <soap:Envelope
      xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
      xmlns:xsd="http://www.w3.org/2001/XMLSchema"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xmlns:ns1="http://tts.itri.org.tw/TTSService/GetConvertStatus"
      soap:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
      <soap:Body>
        <ns1:GetConvertStatus>
            <accountID xsi:type="xsd:string">"""+passwd.itri_acc+"""</accountID>
            <password xsi:type="xsd:string">"""+passwd.itri_pas+"""</password>
            <convertID xsi:type="xsd:int">"""+convID+"""</convertID>
        </ns1:GetConvertStatus>
      </soap:Body>
    </soap:Envelope>
    """).encode('utf-8')

    head = {'Content-Type':'text-xml; charset=utf-8',
        'SOAPAction':'http://tts.itri.org.tw/TTSService/GetConvertStatus'}

    try:
        while True:
            conn.request("POST","/TTSService/Soap_1_3.php", payload, head)
            request = conn.getresponse().read().decode('utf-8')
            result = mdom.parseString(request).getElementsByTagName('Result')[0].firstChild.data
            if(result.split('&')[2] == '2'): # completed
                url = result.split('&')[4]
                break
            time.sleep(0.5)
            print('[T2W] Waiting...')
    except:
        url = ''
        return

    print('[T2W] '+url)

    conn.request("GET",url)
    audio = conn.getresponse().read() # wav as binary
    conn.close()

    return audio
