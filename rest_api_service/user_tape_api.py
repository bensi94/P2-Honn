from flask.views import MethodView
from nameko.standalone.rpc import ClusterRpcProxy
from shared_utils.config import CONFIG
from flask import Response, request
import json

class UserTapeAPI(MethodView):

    # Gets information about the tapes a given user has on loan
    def get(self, user_id):
        with ClusterRpcProxy(CONFIG) as rpc:
            tapes = rpc.tape_service.get_tapes_of_user(user_id)
            if isinstance(tapes, list):
                if tapes == []:
                    return ('User has no tapes on loan', 404)
                return Response(json.dumps(tapes), mimetype='application/json')

            return (tapes['msg'], tapes['code'])

    # Registers tape on loan
    def post(self, user_id, tape_id):
        borrow = {
            'user_id': user_id,
            'tape_id': tape_id,
            'borrow_date': None,
            'return date': None
        }

        with ClusterRpcProxy(CONFIG) as rpc:
            response = rpc.tape_service.register_tape(borrow)
            return(response['msg'], response['code'])
    #  Returns tape that was on loan
    def delete(self, user_id, tape_id):
        with ClusterRpcProxy(CONFIG) as rpc:
            response = rpc.tape_service.return_tape(user_id, tape_id)
            return(response['msg'], response['code'])

    # Updates borrowing information
    def put(self, user_id, tape_id):
        borrow = {
            "user_id": user_id,
            "tape_id": tape_id,
            "borrow_date": request.args.get('borrow_date'),
            "return_date": request.args.get('return_date')
        }

        with ClusterRpcProxy(CONFIG) as rpc:
            response = rpc.tape_service.update_registration(borrow)
            return(response['msg'], response['code'])
