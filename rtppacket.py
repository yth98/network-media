import sys 
from time import time

HEADER_SIZE = 12 


class rtp_packet:
    header = bytearray(HEADER_SIZE)
    def __init__(self):
        pass

    def encode(self, verison, padding, extension, cc, seqnum, marker, pt, ssrc, payload):
        header = bytearray(HEADER_SIZE)
        timestamp = int(time())


        header[0] = (header[0] | verison << 6) & 0xC0
        header[0] = (header[0] | padding << 5)
        header[0] = (header[0] | extension << 4)
        header[0] = (header[0] | (cc & 0x0F))
        header[1] = (header[1] | marker << 7)
        header[1] = (header[1] | (pt & 0x7F))
        header[2] = (seqnum & 0xFF00) >> 8
        header[3] = (seqnum & 0xFF)
        header[4] = (timestamp >> 24)
        header[5] = (timestamp >> 16) & 0xFF
        header[6] = (timestamp >> 8)  & 0xFF 
        header[7] = (timestamp & 0xFF)
        header[8] = (ssrc >> 24)
        header[9] = (ssrc >> 16) & 0xFF
        header[10] = (ssrc >> 8) & 0xFF
        header[11] = ssrc & 0xFF

        self.header = header
        self.payload = payload


    def decode(self, byteStream):
        self.header = bytearray(byteStream[:HEADER_SIZE])
        self.payload = byteStream[HEADER_SIZE:]

    def version(self):
        return int(self.header[0] >> 6)

    def seqnum(self):
        seqnum = self.header[2] << 8 | self.header[3]
        return int(seqnum)

    def timestamp(self):
        timestamp = self.header[4] << 24 | self.header[5] << 16 | self.header[6] << 8 | self.header[7]
        return int(timestamp)

    def payloadtype(self):
        pt = self.header[1] & 127
        return int(pt)

    def getpayload(self):
        return self.payload

    def getPacket(self):
        return self.header + self.payload
