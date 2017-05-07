def setwifi(timeout=35):
    """
    This is ESP8266 micropython script designed to serve ESP8266 as web server to obtain SSID and password
    The script sets up an access point, listens on port 80 and implements following commands:
    'http://<esp8266_ip>'                   - shows web page to enter WiFi info
    """

    import gc
    from setwifi import setup_station
    from time import sleep_ms
    import usocket as socket
    import network
    # create access-point interface
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(True)
    # the AP has to be active to be able to configure it
    try:
        ap_if.config(authmode=network.AUTH_OPEN)
    except Exception as e:
        e_str = str(e)
        if "can't set AP config" in e_str:
            print("Ignoring exception: ".format(e_str))
        else:
            return e
    port = 80
    cfg_data = {}
    sta_if = network.WLAN(network.STA_IF)

    return_code = None
    setup_attempts = 0

    # the following constants are defined because the HTML strings need to match the python strings.
    SSID = "SSID"
    PASSWORD = "password"
    SUBMIT_VALUE = "submit_value"
    CANCEL = "Cancel"
    NETWORK_ID = "Network ID"
    
    MSG_ALREADY_CONNECTED = "WiFi is already connected to a network - hit {} to leave it be."

    html_page = """HTTP/1.1 200 OK
        Content-type:text/html
        Connection: close\n
        <!DOCTYPE html><html>
        <head><title>{title}</title></head>
        <style>body {{background-color: lightblue}} h2 {{color: Red;}}</style>
        <div style=\"display: inline-block; text-align: center; color: Black; align: center; width: 100%\">
        <body><h2>{message}</h2><h3>{body}</h3></body>
        {form}
        </div>
        </html>"""
    
    ssid_form = """<form method=\"POST\">
        {NETWORK_ID}:<br>
        <input type=\"text\" name=\"{SSID}\"><br>
        Password:<br>
        <input type=\"password\" name=\"{PASSWORD}\"><br><br>
        <input type=\"submit\" name =\"{SUBMIT_VALUE}\" style=\"background-color:#00FF80\">
        <input type=\"submit\" name =\"{SUBMIT_VALUE}\" value=\"{CANCEL}\" style=\"background-color:#D8D8D8\">
        </form>"""

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.bind(('', port))
    s.listen(2)
    print('\n-- Now Listening on: {} {}:{}...\n'.format(ap_if.config('essid'), ap_if.ifconfig()[0], port))
    
    page_title = "Configure WiFi"

    try:
        while return_code is None:
            conn, addr = s.accept()
            method = None
            content_length = None
            page_message = ""
            if sta_if.isconnected():
                page_message = MSG_ALREADY_CONNECTED.format(CANCEL)
            page_body = "Please enter your WiFi Info"
            page_form = ssid_form.format(NETWORK_ID=NETWORK_ID, SSID=SSID, PASSWORD=PASSWORD, SUBMIT_VALUE=SUBMIT_VALUE, CANCEL=CANCEL)

            request = conn.recv(1024)

            lines = [d.strip() for d in request.decode('utf-8').split('\r\n')]
            method, raw_path, version = lines[0].split(' ')
#            path = raw_path.split('?', 1)[0]
#            print(" request: {:5} {}".format(method, path))
            headers = {k: v for k, v in
                (l.split(': ') for l in lines[1:-2])}
#                print("  headers: {}".format(headers))
#                host = headers['Host']
#                print("  host: {}".format(host))
            if 'Content-Length' in headers:
                content_length = headers['Content-Length']

            if method == 'POST':
                if content_length is None:
                    print('Error: no content length in POST')
                    page_message = "Browser Error: no content length"
                else:
                    post_data = conn.recv(int(content_length))
                    post_data = post_data.decode('UTF-8')
#                    print('\npost_data: {}'.format(post_data))
                    for i, val in enumerate(post_data.split('&')):
                        (k,v) = val.split('=')
                        cfg_data[k] = v

                    if SUBMIT_VALUE in cfg_data and cfg_data[SUBMIT_VALUE] == CANCEL:
                        page_body="WiFi setup cancelled."
                        page_message=""
                        page_form=""
                        return_code = "cancelled: attempts: " + str(setup_attempts)
                    # could have added javascript validation, but since it can be disabled, its recommended the server do the validation
                    elif SSID not in cfg_data or len(cfg_data[SSID]) < 2 or PASSWORD not in cfg_data or len(cfg_data[PASSWORD]) < 4:
                        if SSID not in cfg_data or len(cfg_data[SSID]) < 2:
                            page_message = "Invalid {}: '{}'".format(NETWORK_ID, cfg_data[SSID])
                        else:
                            page_message = "Invalid {}: '{}'".format(PASSWORD, cfg_data[PASSWORD])
                        cfg_data = {}
                    else:
                        setup_ok, setup_message = setup_station(cfg_data[SSID], cfg_data[PASSWORD])
                        setup_attempts += 1
                        if setup_ok:
                            page_body = setup_message
                            page_form = ""
                            return_code = "done: connected"
                        else:
                            page_message=setup_message
                            cfg_data = {}

            response = html_page.format(title=page_title, message=page_message, body=page_body, form=page_form)
            conn.send(response)
            conn.close()
            gc.collect()

    except Exception as e:
        e_str = str(e)
        if 'ETIMEDOUT' in e_str:
            return_code = "timeout"
        else:
            return_code = "exception: ".format(e_str)

    sleep_ms(2000)
    s.close()
    sleep_ms(2000)
    ap_if.active(False)
    return return_code


def setup_station(id, pw):
    import network
    from time import sleep_ms
    TIMEOUT = 20

    MSG_TIMEOUT = "Failed to connect to WiFi network '{}' within {} seconds - the password might be wrong."
    MSG_NOT_FOUND = "WiFi network '{}' not found."
    MSG_FAILED_TO_CONNECT = "Failed to connect to WiFi network '{}'"
    MSG_BAD_PASSWORD = "Error: incorrect password '{}' for network '{}'"
    MSG_NETWORK_IDLE = "Internal Error: network is idle after being activated."
    MSG_UNRECOGNIZED_STATUS = "Internal Error: unrecognized network interface status: {}"

    message = MSG_TIMEOUT.format(id, TIMEOUT)
    print("\n-- Connecting to network: {}".format(id),end='')
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.disconnect()
    sleep_ms(1000)
    sta_if.connect(id, pw)
    for i in range(TIMEOUT):
        sleep_ms(1000)
        status = sta_if.status()
        if status == network.STAT_CONNECTING:
            print(".",end='')
            continue
        elif status == network.STAT_GOT_IP:
            message = MSG_NOW_CONNECTED.format(id, sta_if.ifconfig()[0])
            break
        elif status == network.STAT_NO_AP_FOUND:
            message = MSG_NOT_FOUND.format(id)
            break
        elif status == network.STAT_CONNECT_FAIL:
            message = MSG_FAILED_TO_CONNECT.format(id)
            break
        elif status == network.STAT_WRONG_PASSWORD:
            # some networks don't give this status - a timeout will occur instead
            message = MSG_BAD_PASSWORD.format(pw,id)
            break
        elif status == network.STAT_IDLE:
            message = MSG_NETWORK_IDLE
            break
        else:
            message = MSG_UNRECOGNIZED_STATUS.format(status)
            break

    print(message)
    return sta_if.isconnected(), message
