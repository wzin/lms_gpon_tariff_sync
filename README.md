Requirements
============

- lms patched with GPON patch from elmat.eu
- /etc/lms/lms.ini filled with proper data
- tarrifs names in format "FTTH-<speed>" and GPON profiles in format
  "<onu-model-name>-<speed>" where 'speed' is a integer pair delimited
with slash e.g.

```
lms tarrif name: FTTH-10/2
gpon profile name: H640GW-02-10/2
```
- python-mysqldb module
- python requests module
- create a lms_url variable in lms.ini pointing to your lms installation

NOTE: only mysql is supported at this time

Usage
=====

- create GPON profiles on OLT
- create tarrifs in LMS
- assign tarrifs to customers
- customer's tarrifs will get automatically mapped to gpon traffic
  profiles


TODO
====
- make per onu-model tarrifs
