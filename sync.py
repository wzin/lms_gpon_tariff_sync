#!/usr/env/python
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import ConfigParser
import MySQLdb
import sys
import time

import requests


class OnuReset:
    def __init__(self):
        self.session = requests.Session()
        self.config = ConfigParser.RawConfigParser()
        self.config.read('/etc/lms/lms.ini')
        self.credentials = {
            'loginform[login]': self.config.get('syncer', 'user'),
            'loginform[pwd]': self.config.get('syncer', 'password'),
            'loginform[submit]': 'Login'
          }

        self.lms_url = self.config.get('syncer', 'lms_url')

        r = self.session.get(self.lms_url)
        r = self.session.post(self.lms_url, data=self.credentials)
        if r.status_code != 200:
            print "Could not open LMS (code %s)" % r.status_code
            sys.exit(1)

    def reset_onu(self, onu_id):
        url = '{}/?m=gpononuedit&id={}'.format(self.lms_url, onu_id)
        print "Sending reset to %s via %s" % (onu_id, url)
        self.session.post(url, data={'onureset' : 1,
                                     'save' : 1,
                                     'snmpsend' : 1,
                                     'onustatus' : 1})

class LmsGponSyncer:
    def __init__(self):
        self.config = self._parse_config()
        self.db = self._connect_to_db()
        self.onu_reset = OnuReset()

    def _parse_config(self):
        config = ConfigParser.RawConfigParser()
        config.read('/etc/lms/lms.ini')
        self.db_type = config.get('database', 'type')
        if self.db_type != 'mysql':
            print "Sorry - only mysql is supported this time"
            sys.exit(1)
        self.db_user = config.get('database', 'user')
        self.db_pass = config.get('database', 'password') 
        self.db_name = config.get('database', 'database') 
        self.db_host = config.get('database', 'host') 
        self.db = self._connect_to_db()
        self.cursor = self.db.cursor()
        self.time = time.strftime("%d/%m/%Y %H:%M:%S")
        return config

    def _connect_to_db(self):
        db = MySQLdb.connect(self.db_host,
                             self.db_user,
                             self.db_pass,
                             self.db_name,
                             )
        db.autocommit(True)
        return db

    def run(self):
        query = 'select gponoltprofiles.name, gpononu.host_id1 as node_id , nodes.name,  tariffs.name as tariff_name, gpononu.id from gpononu join gponoltprofiles on gpononu.gponoltprofilesid = gponoltprofiles.id join nodes on nodes.id = gpononu.host_id1 join nodeassignments on nodeassignments.nodeid = nodes.id join assignments on assignments.id = nodeassignments.assignmentid join tariffs on tariffs.id = assignments.tariffid;'
        self.cursor.execute(query)
        data = self.cursor.fetchall()
        self._parse_tariffs(data)

    def _parse_tariffs(self, data):
        for row in data:
            gpon_profile = row[0]
            gpon_node_id = row[4]
            lms_node_id = row[1]
            lms_node_name = row[2]
            lms_tariff_name = row[3]

            actual_speed = gpon_profile.split('-')[-1]
            set_speed = lms_tariff_name.split('-')[-1] 
            if actual_speed != set_speed:
                print 'Detected tariffs to sync for gpon node id = %s' % gpon_node_id
                print 'Actual speed => %s and lms speed => %s' % (actual_speed, set_speed)
                self._sync_tariff(gpon_node_id, set_speed)

    def _select_onu_profile_by_speed(self, speed):
        select_query = "select id from gponoltprofiles where name like '%-{}';".format(speed)
        self.cursor.execute(select_query)
        gpon_host_id = self.cursor.fetchone()
        return gpon_host_id

    def _sync_tariff(self, gpon_node_id, set_speed):
        gpon_profile_id = self._select_onu_profile_by_speed(set_speed)
        gpon_node_id = gpon_node_id
        print '%s => Updating %s with speed %s' % (self.time, gpon_node_id, set_speed)
        update_query = 'update gpononu set gponoltprofilesid = %s where id = %s' % (int(gpon_profile_id[0]), gpon_node_id)
        print update_query
        self.cursor.execute(update_query)
        self.db.commit()
        self.onu_reset.reset_onu(gpon_node_id),

    def _push_to_onu(self):
        pass

if __name__ == "__main__":
    lgs = LmsGponSyncer()
    lgs.run()
    lgs.db.close()
