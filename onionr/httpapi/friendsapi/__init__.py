'''
    Onionr - Private P2P Communication

    This file creates http endpoints for friend management
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
import core, json
from onionrusers import contactmanager
from flask import Blueprint, Response, request, abort, redirect

friends = Blueprint('friends', __name__)

@friends.route('/friends/list')
def list_friends():
    pubkey_list = {}
    friend_list = contactmanager.ContactManager.list_friends(core.Core())
    for friend in friend_list:
        pubkey_list[friend.publicKey] = {'name': friend.get_info('name')}
    return json.dumps(pubkey_list)

@friends.route('/friends/add/<pubkey>', methods=['POST'])
def add_friend(pubkey):
    contactmanager.ContactManager(core.Core(), pubkey, saveUser=True).setTrust(1)
    return redirect(request.referrer + '#' + request.form['token'])

@friends.route('/friends/remove/<pubkey>', methods=['POST'])
def remove_friend(pubkey):
    contactmanager.ContactManager(core.Core(), pubkey).setTrust(0)
    return redirect(request.referrer + '#' + request.form['token'])

@friends.route('/friends/setinfo/<pubkey>/<key>', methods=['POST'])
def set_info(pubkey, key):
    data = request.form['data']
    contactmanager.ContactManager(core.Core(), pubkey).set_info(key, data)
    return redirect(request.referrer + '#' + request.form['token'])

@friends.route('/friends/getinfo/<pubkey>/<key>')
def get_info(pubkey, key):
    retData = contactmanager.ContactManager(core.Core(), pubkey).get_info(key)
    if retData is None:
        abort(404)
    else:
        return retData