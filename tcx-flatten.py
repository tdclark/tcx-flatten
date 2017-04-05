#!/usr/bin/env pyhton2.7

import argparse
import collections
import datetime
import json
import os
import sys

import xml.etree.ElementTree as ElementTree

NAMESPACE = '{http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2}'

Activity = collections.namedtuple('Activity', 'id, timestamp, trackpoints')
Trackpoint = collections.namedtuple('Trackpoint', 'latitude, longitude, altitude_meters, timestamp')

def parse_trackpoint_node(trackpoint_node):
    """Parse a trackpoint node into a trackpoint, returning None if not valid."""
    latitude_node = trackpoint_node.find('{0}Position/{0}LatitudeDegrees'.format(NAMESPACE))
    longitude_node = trackpoint_node.find('{0}Position/{0}LongitudeDegrees'.format(NAMESPACE))
    altitude_meters_node = trackpoint_node.find('{}AltitudeMeters'.format(NAMESPACE))

    if latitude_node is None or longitude_node is None:
        return None

    latitude = latitude_node.text
    longitude = longitude_node.text
    timestamp = trackpoint_node.find('{}Time'.format(NAMESPACE)).text
    if altitude_meters_node is None:
        altitude_meters = None
    else:
        altitude_meters = altitude_meters_node.text

    return Trackpoint(latitude, longitude, altitude_meters, timestamp)

def parse_tcx_file(tcx_filename):
    """Parse a TCX file into a list of activities."""

    activities = list()
    root = ElementTree.parse(tcx_filename).getroot()
    activity_nodes = root.findall('.//{}Activity'.format(NAMESPACE))

    for activity_node in activity_nodes:
        activity_id = activity_node.find('{}Id'.format(NAMESPACE)).text
        activity_timestamp = activity_id
        activity_trackpoints = list()

        trackpoint_nodes = activity_node.findall('.//{}Trackpoint'.format(NAMESPACE))
        for trackpoint_node in trackpoint_nodes:
            trackpoint = parse_trackpoint_node(trackpoint_node)
            if trackpoint is not None:
                activity_trackpoints.append(trackpoint)

        activity = Activity(activity_id, activity_timestamp, activity_trackpoints)
        activities.append(activity)

    return activities

def get_output_data(activities):
    output_activities = list()
    for activity in activities:
        output_trackpoints = list()
        for trackpoint in activity.trackpoints:
            #Trackpoint = collections.namedtuple('Trackpoint', 'latitude, longitude, altitude_meters, timestamp')
            output_trackpoint = {
                    "latitude": trackpoint.latitude,
                    "longitude": trackpoint.longitude,
                    "altitude_meters": trackpoint.altitude_meters,
                    "timestamp": trackpoint.timestamp
            }

            output_trackpoints.append(output_trackpoint)

        output_activity = {
            "id": activity.id,
            "timestamp": activity.timestamp,
            "trackpoints": output_trackpoints
        }

        output_activities.append(output_activity)

    return {"activities": output_activities}


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('files', metavar='FILES', nargs='+', help='TCX files to process')

	args = parser.parse_args()

	activities = list()
	for tcx_file in args.files:
            activities.extend(parse_tcx_file(tcx_file))

        output_data = get_output_data(activities)

	utc_timestamp = datetime.datetime.utcnow().isoformat().replace(':', '-')
	output_filename = "{}_activities.json".format(utc_timestamp)

        with open(output_filename, 'wb') as output:
            json.dump(output_data, output)

        print("Wrote output to {}".format(output_filename))


if __name__ == '__main__':
    sys.exit(main())
