import transcriber.settings as settings
from transcriber.messages import Activity, IpalMessage
from transcribers.transcriber import Transcriber

# RFC 8446 & RFC 5246
class TLSTranscriber(Transcriber):
    _name = "tls"

    _content_types = {
        20 : "change_cipher_spec",
        21 : "alert",
        22 : "handshake",
        23 : "application_Data",
        24 : "heartbeat",
        25 : "tls12_cid",
        26 : "ACK",
    }

    _handshake_types = {
        0 : "hello_requests",
        1 : "client_hello",
        2 : "server_hello",
        4 : "new_session_ticket",
        5 : "end_of_early_data",
        8 : "encrypted_extension",
        11 : "certificate",
        12 : "server_key_exchange",
        13 : "certificate_request",
        14 : "server_hello_done",
        15 : "certificate_verify",
        16 : "client_key_exchange",
        20 : "finished",
        24 : "key_update",
        254 : "message_hash",
    }

    _alert_level = {
        1 : "warning",
        2 : "fatal",
    }

    _alert_description = {
        0 : "close_notify",
        10 : "unexpected_message",
        20 : "bad_record_mac",
        21 : "decryption_failed_RESERVED",
        22 : "record_overflow",
        30 : "decompression_failure",
        40 : "handshake_failure",
        41 : "no_certificate_RESERVED",
        42 : "bad_certificate",
        43 : "unsupported_certificate",
        44 : "certificate_revoked",
        45 : "certificate_expired",
        46 : "certificate_unknown",
        47 : "illegal_parameter",
        48 : "unknown_ca",
        49 : "access_denied",
        50 : "decode_error",
        51 : "decrypt_error",
        60 : "export_restriction_RESERVED",
        70 : "protocol_version",
        71 : "insufficient_security",
        80 : "internal_error",
        86 : "inappropriate_fallback",
        90 : "user_canceled",
        100 : "no_renegotiation",
        109 : "missong_extension",
        110 : "unsupported_extension",
        112 : "unrecognized_name",
        113 : "bad_certificate_status_response",
        115 : "unkown_psk_identity",
        116 : "certificate_required",
        120 : "no_application_protocol",
    }

    def matches_protocol(self, pkt):
        return "TLS" in pkt
    
    def parse_packet(self, pkt):
        src = "{}:{}".format(pkt["IP"].src, pkt["TCP"].srcport)
        dest = "{}:{}".format(pkt["IP"].dst, pkt["TCP"].dstport)

        match pkt["TLS"].record_content_type: # Python 3.10 ok?
            case 21: # alert
                content_type = self._content_types.get(pkt["TLS"].record_content_type) + "-" + self._alert_level.get(pkt["TLS"].alert_level) + "-" + self._alert_description.get(pkt["TLS"].alert_description)
            case 22: # handshake
                content_type = self._content_types.get(pkt["TLS"].record_content_type) + "-" + self._handshake_types.get(pkt["TLS"].handshake_type)

            case _: # rest 
                content_type = self._content_types.get(pkt["TLS"].record_content_type)
                if content_type == None:
                    content_type = "not_supported"
        
        m = IpalMessage(
            id = self._id_counter.get_next_id(),
            timestamp = float(pkt.sniff_time.timestamp()),
            protocol = self._name,
            src = src,
            dest = dest, 
            length = pkt["TLS"].record_length, # whole record layer, not just alert/change_cipher/app
            crc = "",#TODO überhaupt zu unterscheiden von app data?,
            type = content_type,
            activity = Activity.UNKNOWN,
            flow = "{} - {}".format(src, dest) # hier vielleicht noch type?
        )
        ## request / response stuff
        # + nur für handshake?

        ## data
        # Handshake
        # + Session ID
        # + cipher suits
        # + compression
        # + Extensions
        # + cert?!
        # + finish -> verify data?
        # + TLS Session Ticket  - lifetime hint
        #                       - ticket selber
        # Application data
        # + data length? -> sagt eigentlich nichts aus
        # alert
        # + maybe something interesting?

        # TODO: Session resumption angucken

        return m
    
    def match_response(self, requests, response):
        return