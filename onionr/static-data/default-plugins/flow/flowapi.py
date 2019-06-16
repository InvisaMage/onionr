'''
    Onionr - P2P Microblogging Platform & Social network

    This file primarily serves to allow specific fetching of flow board messages
'''
'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

from flask import Response, request, redirect, Blueprint, abort

flask_blueprint = Blueprint('flow', __name__)

@flask_blueprint.route('/flow/getpostsbyboard/<board>')
def get_post_by_board(board):
    return Response('WIP')