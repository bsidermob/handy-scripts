# This creates an endpoint monitor in Site 24x7
# If monitor already exists, nothing's done.
# Usage:
# python create_endpoint_monitor.py  --refresh_token "1000.123ec284c6431633709d7f18299b2419.00a76b782463fd6daef07b1ea85f5232" \
# --endpoint "https://endpoint.com.au" --monitor_name "My Monitor"
# 
# OAuth refresh_token has to be updated beforehand from Site 24x7
# Here:
# https://accounts.zoho.com/apiauthtoken/create?SCOPE=Site24x7/site24x7api
# More info on the API here: https://www.site24x7.com/help/api/#oauth
# After initial access token has been generated in GUI, perform a curl request to the API to get the refresh token.
#
import requests
import json
import argparse
import logging
import urllib
import simplejson
import sys

client_id = '' # fill this in
client_secret = '' # fill this in
token_url = 'https://accounts.zoho.com/oauth/v2/token'

# Initiliase logger
logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s: %(message)s',
					stream=sys.stdout)
log = logging

def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('--refresh_token', required=True,
						help='refresh token generated from access token')
	parser.add_argument('--monitor_name', required=True,
						help='Friendly site24x7 monitor name')
	parser.add_argument('--endpoint', required=True,
						help='URL/endpoint to monitor')
	global args
	args = parser.parse_args()

def fetch_token(token):
	data = {'client_id':client_id,
			'client_secret':client_secret,
			'refresh_token':token,
			'grant_type':'refresh_token'}
			
	r = requests.post(url = token_url, data = data)
	access_token = json.loads(r.text)['access_token']
	return access_token
	
def get_location_profile_id(name_mask,token):
	val = False
	headers = {'Accept':'application/json; version=2.0',
			   'Authorization':'Zoho-oauthtoken %s' % token}
	url = "https://www.site24x7.com/api/location_profiles"
	try:
		r = requests.get(url = url, headers = headers)
		array = json.loads(r.text)
	except:
		raise Exception('Failed to obtain location profile id')
	for i in array['data']:
		if name_mask in i['profile_name']:
			log.info('Using Site 24x7 profile "' + i['profile_name'] + '"')
			val = i['profile_id']
	if val:
		return val
	else:
		log.error('Location profile with mask "%s" not found' % name_mask)
		raise Exception

			
def get_monitor_group_id(name_mask,token):
	val = False
	headers = {'Accept':'application/json; version=2.0',
			   'Authorization':'Zoho-oauthtoken %s' % token}
	url = "https://www.site24x7.com/api/monitor_groups"
	try:
		r = requests.get(url = url, headers = headers)
		array = json.loads(r.text)
	except:
		raise Exception('Failed to obtain monitor group id')
	for i in array['data']:
		if name_mask in i['display_name']:
			log.info('Using Site 24x7 monitor group "' + i['display_name'] + '"')
			val = i['group_id']
	if val:
		return val
	else:
		log.error('Monitor group with mask "%s" not found' % name_mask)
		raise Exception

			
def get_notification_profile_id(name_mask,token):
	val = False
	headers = {'Accept':'application/json; version=2.0',
			   'Authorization':'Zoho-oauthtoken %s' % token}
	url = "https://www.site24x7.com/api/notification_profiles"
	try:
		r = requests.get(url = url, headers = headers)
		array = json.loads(r.text)
	except:
		raise Exception('Failed to obtain notification profile id')
	for i in array['data']:
		if name_mask in i['profile_name']:
			log.info('Using Site 24x7 notification profile "' + i['profile_name'] + '"')
			val = i['profile_id']
	if val:
		return val
	else:
		log.error('Notification profile with mask "%s" not found' % name_mask)
		raise Exception

def get_monitor_id_by_name(name_mask,token):
	encoded_name = urllib.quote_plus(name_mask)
	val = False
	headers = {'Accept':'application/json; version=2.0',
			   'Authorization':'Zoho-oauthtoken %s' % token}
	url = "https://www.site24x7.com/api/monitors/name/" + encoded_name
	try:
		r = requests.get(url = url, headers = headers)
		array = json.loads(r.text)
	except:
		pass
	try:
		log.info('Found existing Site 24x7 monitor "' + array['data']['display_name'] + '"' + " with ID " + array['data']['monitor_id'])
		val = array['data']['monitor_id']
		return val
	except:
		log.info("Monitor '" + name_mask + "' not found")
		return False
		
def create_rest_api_monitor(monitor_name,endpoint,location_profile_id,notification_profile_id,monitor_group_id,token):
	threshold_profile_id = '248129000000451165'
	user_group_id = '248129000000025003'
	data = {'website': endpoint,
			'check_frequency': '1',
			'threshold_profile_id': threshold_profile_id,
			'type': 'RESTAPI',
			'display_name': monitor_name,
			'user_group_ids': [user_group_id],
			'timeout': 10,
			'monitor_groups': [monitor_group_id],
			'auth_method': 'B',
			'http_method': 'G',
			'notification_profile_id': notification_profile_id,
			'location_profile_id': location_profile_id}
			
	data_json = simplejson.dumps(data)
	headers = {'Content-Type': 'application/json;charset=UTF-8',
			   'Accept':'application/json; version=2.0',
			   'Authorization':'Zoho-oauthtoken %s' % token}
	url = "https://www.site24x7.com/api/monitors"
	r = requests.post(url = url, headers = headers, data = data_json)
	if r.status_code == 201:
		log.info("Monitor " + monitor_name + " has been created")
	else:
		log.error("Create monitor " + monitor_name + " failed with status code " + str(r.status_code))
		log.error(r.text)
		raise Exception

def determine_region(endpoint):
	log.info("using endpoint: " + endpoint)
	if '.au.' in endpoint:
		location = "AU"
		log.info("Determined region from URL as AU")
	elif '.nz.' in endpoint:
		location = "AU"
		log.info("Determined region from URL as NZ. Using AU region.")
	elif '.us.' in endpoint:
		location = "US"
		log.info("Determined region from URL as US")
	else:
		log.info("Can't determine region from URL. Defaulting to AU")
		location = "AU"
	return location
	
def determine_environment(endpoint):
	if '.prd.' in endpoint:
		environment = "PROD"
		log.info("Determined environment from URL as PROD")
	elif '.npd.' in endpoint:
		environment = "NON PROD"
		log.info("Determined environment from URL as NON PROD")
	return environment
		
def determine_profile_names(region,environment):
	monitor_group_name = region + ' ' + environment
	location_profile_name = region + ' - on-premise'
	
	if environment == "NON PROD":
		notification_profile_name = 'AU NONPROD Notification'
	if environment == "PROD":
		notification_profile_name = 'AU PROD Notification'
	
	d = dict()
	d['monitor_group_name'] = monitor_group_name
	d['notification_profile_name'] = notification_profile_name
	d['location_profile_name'] = location_profile_name
	return d
		
def main():
	parse_args()
	monitor_name = args.monitor_name
	endpoint = args.endpoint
	region = determine_region(endpoint)
	environment = determine_environment(endpoint)
	monitor_group_name = determine_profile_names(region,environment)['monitor_group_name']
	notification_profile_name = determine_profile_names(region,environment)['notification_profile_name'] 
	location_profile_name = determine_profile_names(region,environment)['location_profile_name']
	token = fetch_token(args.refresh_token)
	location_profile_id = get_location_profile_id(location_profile_name,token)
	monitor_group_id = get_monitor_group_id(monitor_group_name,token)
	notification_profile_id = get_notification_profile_id(notification_profile_name,token)
	if get_monitor_id_by_name(monitor_name,token):
		log.info("Monitor already exists. Not creating new one.")
	else:
		log.info("Monitor doesn't exist yet. Creating.")
		create_rest_api_monitor(monitor_name,endpoint,
								location_profile_id,notification_profile_id,monitor_group_id,token)

main()
