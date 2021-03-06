# -*- coding: utf-8 -*-
#
#    LinOTP - the open source solution for two factor authentication
#    Copyright (C) 2010 - 2017 KeyIdentity GmbH
#
#    This file is part of LinOTP server.
#
#    This program is free software: you can redistribute it and/or
#    modify it under the terms of the GNU Affero General Public
#    License, version 3, as published by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the
#               GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
#    E-mail: linotp@keyidentity.com
#    Contact: www.linotp.org
#    Support: www.keyidentity.com
#
'''handle all configuration items with aspekts like persitance and
   syncronysation and provides this to all requests
'''

import logging
import copy

from pylons import tmpl_context as c

from linotp.lib.config.parsing import parse_config
from linotp.lib.config.config_class import LinOtpConfig
from linotp.lib.config.util import expand_here
from linotp.lib.config.db_api import _retrieveAllConfigDB


log = logging.getLogger(__name__)

linotp_config = None
linotp_config_tree = None


def refresh_config():

    """
    retrieves all config entries from the database and rewrites the
    global linotp_config object
    """

    global linotp_config
    linotp_config, delay = _retrieveAllConfigDB()


###############################################################################
#     public interface
###############################################################################


def getLinotpConfig():

    '''
    return the thread local dict with all entries

    :return: local config dict
    :rtype: dict
    '''

    global linotp_config
    global linotp_config_tree

    # TODO: replication

    if linotp_config is None:
        refresh_config()

    if linotp_config_tree is None:
        linotp_config_tree = parse_config(linotp_config)

    ret = {}
    try:
        if not hasattr(c, 'linotpConfig'):
            c.linotpConfig = LinOtpConfig()

        ty = type(c.linotpConfig).__name__
        if ty != 'LinOtpConfig':
            try:
                c.linotpConfig = LinOtpConfig()
            except Exception as exx:
                log.exception("Could not add LinOTP configuration to pylons "
                              "tmpl_context. Exception was: %r", exx)
                raise exx
        ret = c.linotpConfig

        if ret.delay is True:
            if hasattr(c, 'hsm') is True and isinstance(c.hsm, dict):
                hsm = c.hsm.get('obj')
                if hsm is not None and hsm.isReady() is True:
                    ret = LinOtpConfig()
                    c.linotpConfig = ret

    except Exception as exx:
        log.debug("Bad Hack: Retrieving LinotpConfig without "
                  "controller context")
        ret = LinOtpConfig()

        if ret.delay is True:
            if hasattr(c, 'hsm') is True and isinstance(c.hsm, dict):
                hsm = c.hsm.get('obj')
                if hsm is not None and hsm.isReady() is True:
                    ret = LinOtpConfig()

    return ret


# ########## external interfaces ###############


def storeConfig(key, val, typ=None, desc=None):

    log_val = val
    if typ and typ == 'password':
        log_val = "X" * len(val)
    log.debug('Changing config entry %r: New value is %r', key, log_val)

    conf = getLinotpConfig()
    conf.addEntry(key, val, typ, desc)
    return True


def updateConfig(confi):
    '''
    update the server config entries incl. syncing it to disc
    '''
    conf = getLinotpConfig()

    # remember all key, which should be processed
    p_keys = copy.deepcopy(confi)

    typing = False

    for entry in confi:
        typ = confi.get(entry + ".type", None)
        des = confi.get(entry + ".desc", None)

        # check if we have a descriptive entry
        if typ is not None or des is not None:
            typing = True
            if typ is not None:
                del p_keys[entry + ".type"]
            if des is not None:
                del p_keys[entry + ".desc"]

    if typing is True:
        # tupple dict containing the additional info
        t_dict = {}
        for entry in p_keys:
            val = confi.get(entry)
            typ = confi.get(entry + ".type", None)
            des = confi.get(entry + ".desc", None)
            t_dict[entry] = (val, typ or "string", des)

        for key in t_dict:
            (val, typ, desc) = t_dict.get(key)
            if val in [str, unicode] and "%(here)s" in val:
                val = expand_here(val)
            conf.addEntry(key, val, typ, desc)

    else:
        conf_clean = {}
        for key, val in confi.iteritems():
            if "%(here)s" in val:
                val = expand_here(val)
            conf_clean[key] = val

        conf.update(conf_clean)

    return True


def getFromConfig(key, defVal=None):
    conf = getLinotpConfig()
    value = conf.get(key, defVal)
    return value


def refreshConfig():
    conf = getLinotpConfig()
    conf.refreshConfig(do_reload=True)
    return


def removeFromConfig(key, iCase=False):
    log.debug('Removing config entry %r' % key)
    conf = getLinotpConfig()

    if iCase is False:
        if key in conf:
            del conf[key]
    else:
        # case insensitive delete
        # #- might have multiple hits
        fConf = []
        for k in conf:
            if (k.lower() == key.lower() or
               k.lower() == 'linotp.' + key.lower()):
                fConf.append(k)

        if len(fConf) > 0:
            for k in fConf:
                if k in conf or 'linotp.' + k in conf:
                    del conf[k]

    return True


# several config functions to follow
def setDefaultMaxFailCount(maxFailCount):
    return storeConfig(u"DefaultMaxFailCount", maxFailCount)


def setDefaultSyncWindow(syncWindowSize):
    return storeConfig(u"DefaultSyncWindow", syncWindowSize)


def setDefaultCountWindow(countWindowSize):
    return storeConfig(u"DefaultCountWindow", countWindowSize)


def setDefaultOtpLen(otpLen):
    return storeConfig(u"DefaultOtpLen", otpLen)


def setDefaultResetFailCount(resetFailCount):
    return storeConfig(u"DefaultResetFailCount", resetFailCount)

# eof #########################################################################
