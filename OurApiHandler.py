from urllib.parse import urlparse, parse_qsl
from http.server import BaseHTTPRequestHandler
from database_controller import DatabaseController
import json


class OurApiHandler(BaseHTTPRequestHandler):
    request_text_change = None
    client_text_change = None
    response_text_change = None
    definitions = None
    definitions_dict = {}
    request = ''
    client = ''
    body = ''

    def do_GET(self):
        result_json = ''

        # check the path is correct
        query_function = self.trim_path(urlparse(self.path).path)

        # if query_function returns False the API path could not be found
        if not query_function:
            return

        # split all parameters into a dictionary
        query_args = dict(parse_qsl(urlparse(self.path).query))

        # check query_function is a key in the definitions_dict
        if self.request_has_function(query_function):

            if not self.request_query_has_errors(query_function, query_args):
                db = DatabaseController()
                sql = self.definitions_dict[query_function]['sql']

                # run the query on the DB
                self.body = result_json = db.run_query(sql, query_args)

                self._set_response(200)
                self.wfile.write(result_json.encode('utf-8'))

                if self.path[-3:] != 'ico':
                    self.request_text_change.emit(self.command
                                                  + ","
                                                  + self.path)
                    client_address, client_port = self.client_address
                    self.client_text_change.emit("Client IP Address "
                                                 + str(client_address)
                                                 + " and port "
                                                 + str(client_port))
                    self.response_text_change.emit(self.body)

        return

    def trim_path(self, path):
        if path.find('/api/', 0, len(path)) >= 0:
            return path.replace('/api/', '')
        else:
            result_json = 'Supplied path not found: ' + path
            self._set_path_not_found_response()
            self.wfile.write(result_json.encode('utf-8'))

        return False

    def request_query_has_errors(self, query_function, query_args):
        config_args = self.definitions_dict[query_function]

        # check the required config_args are present in the query_args
        args_error = False
        args_error_list = []
        for arg in config_args['args']:
            if arg not in query_args:
                args_error = True
                args_error_list.append(arg)

        if args_error:
            result_json = 'Query Parameter/s expected: ' \
                           + json.dumps(args_error_list) \
                          + '\nQuery Parameter/s supplied: ' \
                          + json.dumps(list(query_args.keys()))

            self._set_missing_argument_response()
            self.wfile.write(result_json.encode('utf-8'))
            return True

        return False

    def request_has_function(self, query_function):
        self.definitions.load()
        self.definitions_dict = self.definitions.definitions_dict
        if query_function in self.definitions_dict:
            return True
        else:
            result_json = 'API function/s expected: '\
                          + json.dumps(list(self.definitions_dict.keys()))\
                          + '\nFunction supplied: ' \
                          + json.dumps(query_function)
            self._set_missing_function_response()
            self.wfile.write(result_json.encode('utf-8'))
            return False

    def _set_response(self, code):
        self.send_response(code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def _set_missing_argument_response(self):
        self._set_response(422)

    def _set_missing_function_response(self):
        self._set_response(404)

    def _set_path_not_found_response(self):
        self._set_response(404)

    def set_definitions(self, definitions):
        self.definitions = definitions

    def set_text_signaller(self, signal_function):
        self.request_text_change = signal_function

    def set_client_signaller(self, signal_function):
        self.client_text_change = signal_function

    def set_response_signaller(self, signal_function):
        self.response_text_change = signal_function