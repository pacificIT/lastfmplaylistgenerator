"""
    Script for generating smart playlists based on a seeding track and last.fm api
	Created by: ErlendSB
"""

import os
import httplib, urllib, urllib2
import sys
import xbmc, xbmcgui
from urllib import quote_plus, unquote_plus
import re

class Main:
	countFoundTracks = 0
	foundTracks = []
	currentSeedingTrack = 0
	maxRetries = 5
	
	def __init__( self ):

		if xbmc.Player().isPlayingAudio() == False:
			self.close()

		currentlyPlayingTitle = xbmc.Player().getMusicInfoTag().getTitle()
		currentlyPlayingArtist = xbmc.Player().getMusicInfoTag().getArtist()
		countFoundTracks = 0
		xbmc.PlayList(0).clear()
		self.fetch_similarTracks(currentlyPlayingTitle,currentlyPlayingArtist)
		 
			
	def fetch_similarTracks( self, currentlyPlayingTitle, currentlyPlayingArtist ):
		SCRIPT_NAME = "LAST.FM Playlist generator"
		uriPB = xbmcgui.DialogProgress()
		uriPB.create(SCRIPT_NAME, 'Finding similar tracks')
		uriPB.update(0, 'Querying Last.FM for: ' + currentlyPlayingTitle + " by: " + currentlyPlayingArtist , str(self.countFoundTracks) + " found so far")   
		apiPath = 'http://ws.audioscrobbler.com/2.0/?method=track.getsimilar'
		apiKey = "71e468a84c1f40d4991ddccc46e40f1b"

		options = '&api_key=' + apiKey

		# The url in which to use
		Base_URL = apiPath + "&artist=" + currentlyPlayingArtist.replace(" ","+") + "&track=" + currentlyPlayingTitle.replace(" ","+") + options

		WebSock = urllib.urlopen(Base_URL)  # Opens a 'Socket' to URL
		WebHTML = WebSock.read()            # Reads Contents of URL and saves to Variable
		WebSock.close()                     # Closes connection to url

		xbmc.executehttpapi("setresponseformat(openRecordSet;<recordset>;closeRecordSet;</recordset>;openRecord;<record>;closeRecord;</record>;openField;<field>;closeField;</field>)");

		similarTracks = re.findall("<track>.+?<name>(.+?)</name>.+?<artist>.+?<name>(.+?)</name>.+?</artist>.+?</track>", WebHTML, re.DOTALL )
		countTracks = len(similarTracks)
		progressIncrement = countTracks / 100
		percentComplete = 0
		print "Count: " + str(countTracks)
		for similarTrackName, similarArtistName in similarTracks:
			percentComplete = percentComplete + progressIncrement;
			#print "Looking for: " + similarTrackName + " - " + similarArtistName
			similarTrackName = similarTrackName.replace("+"," ").replace("("," ").replace(")"," ").replace("&quot","'").replace("'","''").replace("&amp;","and")
			similarArtistName = similarArtistName.replace("+"," ").replace("("," ").replace(")"," ").replace("&quot","'").replace("'","''").replace("&amp;","and")
			sql_music = "select strTitle, strArtist, strAlbum, strPath, strFileName from songview where strTitle LIKE '%%" + similarTrackName + "%%' and strArtist LIKE '%%" + similarArtistName + "%%' limit 1"
			music_xml = xbmc.executehttpapi( "QueryMusicDatabase(%s)" % quote_plus( sql_music ), )
			# separate the records
			records = re.findall( "<record>(.+?)</record>", music_xml, re.DOTALL )
			for count, item in enumerate( records ):
				# separate individual fields
				fields = re.findall( "<field>(.*?)</field>", item, re.DOTALL )
				artist = fields[1]
				trackTitle = fields[0]
				trackPath = fields[3] + fields[4]
				print "Found: " + trackTitle + " by: " + artist
				if (similarTrackName + '|' + similarArtistName not in self.foundTracks):
					xbmc.PlayList(0).add(trackPath)
					self.countFoundTracks += 1
					self.foundTracks += [similarTrackName + '|' + similarArtistName]
			
			uriPB.update(percentComplete, 'Finding similar tracks to: ' + currentlyPlayingTitle + " by: " + currentlyPlayingArtist, str(self.countFoundTracks) + " found so far - (try:" + str(self.currentSeedingTrack) + "/" + str(self.maxRetries) +")" )   

			
		if (self.countFoundTracks < 25 and len(self.foundTracks) > self.currentSeedingTrack and self.currentSeedingTrack < self.maxRetries):
			print "TOO few results. Trying again with: " + self.foundTracks[self.currentSeedingTrack]
			similarTrackName =self.foundTracks[self.currentSeedingTrack].split('|')[0]
			similarArtistName =self.foundTracks[self.currentSeedingTrack].split('|')[1]
			self.currentSeedingTrack += 1
			self.fetch_similarTracks(similarTrackName,similarArtistName)

			uriPB.update(100, 'Taking you to your playlist...')
		uriPB.close()
		#xbmc.PlayList(0).add(url= xbmc.Player().getMusicInfoTag().getURL(), index=0)
		#xbmc.executehttpapi('setplaylistsong(0)')
		xbmc.executebuiltin('XBMC.ActivateWindow(10500)')
	
if ( __name__ == "__main__" ):
    Main()
