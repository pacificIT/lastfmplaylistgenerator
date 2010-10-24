"""
    Script for generating smart playlists based on a seeding track and last.fm api
	Created by: ErlendSB
"""

import os
import httplib, urllib, urllib2
import sys, time
import xbmc, xbmcgui
from urllib import quote_plus, unquote_plus
import re

class Main:
	countFoundTracks = 0
	foundTracks = []
	currentSeedingTrack = 0
	maxRetries = 5
	apiPath = "http://ws.audioscrobbler.com/2.0/?api_key=71e468a84c1f40d4991ddccc46e40f1b"
	
	def __init__( self ):

		if xbmc.Player().isPlayingAudio() == False:
			return False

		currentlyPlayingTitle = xbmc.Player().getMusicInfoTag().getTitle()
		currentlyPlayingArtist = xbmc.Player().getMusicInfoTag().getArtist()
		countFoundTracks = 0
		xbmc.PlayList(0).clear()
		xbmc.PlayList(0).add(url= xbmc.Player().getMusicInfoTag().getURL(), index=0)
		self.foundTracks += [currentlyPlayingTitle + '|' + currentlyPlayingArtist]
		#xbmc.executebuiltin( "AddToPlayList(" + xbmc.Player().getMusicInfoTag().getURL() + ";0)")

		#xbmc.executehttpapi('setplaylistsong(0)')
		self.fetch_similarTracks(currentlyPlayingTitle,currentlyPlayingArtist)
		 
	
	# def fetch_similarArtists( self, currentlyPlayingArtist):
		# apiMethod = "&method=artist.getsimilar"

		# # The url in which to use
		# Base_URL = self.apiPath + apiMethod + "&artist=" + currentlyPlayingArtist.replace(" ","+")

		# WebSock = urllib.urlopen(Base_URL)  # Opens a 'Socket' to URL
		# WebHTML = WebSock.read()            # Reads Contents of URL and saves to Variable
		# WebSock.close()                     # Closes connection to url

		# xbmc.executehttpapi("setresponseformat(openRecordSet;<recordset>;closeRecordSet;</recordset>;openRecord;<record>;closeRecord;</record>;openField;<field>;closeField;</field>)");

		# similarArtists = re.findall("<artist>.+?<name>(.+?)</name>.+?</artist>", WebHTML, re.DOTALL )
		# for similarArtistName in similarArtists:
			# return similarArtistName
		

	def fetch_similarTracks( self, currentlyPlayingTitle, currentlyPlayingArtist ):
		SCRIPT_NAME = "LAST.FM Playlist generator"
		uriPB = xbmcgui.DialogProgress()
		uriPB.create(SCRIPT_NAME, 'Finding similar tracks')
		uriPB.update(0, str(self.countFoundTracks) + " found so far - (try:" + str(self.currentSeedingTrack + 1) + "/" + str(self.maxRetries) +")" )   
		apiMethod = "&method=track.getsimilar"

		# The url in which to use
		Base_URL = self.apiPath + apiMethod + "&artist=" + currentlyPlayingArtist.replace(" ","+") + "&track=" + currentlyPlayingTitle.replace(" ","+")
		print Base_URL
		WebSock = urllib.urlopen(Base_URL)  # Opens a 'Socket' to URL
		WebHTML = WebSock.read()            # Reads Contents of URL and saves to Variable
		WebSock.close()                     # Closes connection to url

		xbmc.executehttpapi("setresponseformat(openRecordSet;<recordset>;closeRecordSet;</recordset>;openRecord;<record>;closeRecord;</record>;openField;<field>;closeField;</field>)");

		similarTracks = re.findall("<track>.+?<name>(.+?)</name>.+?<artist>.+?<name>(.+?)</name>.+?</artist>.+?</track>", WebHTML, re.DOTALL )
		countTracks = len(similarTracks)
		progressIncrement = 1
		if (countTracks > 0):
			progressIncrement = float(100 / float(countTracks))
		percentComplete = 0
		#print "Count: " + str(countTracks)
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
				#print "Found: " + trackTitle + " by: " + artist
				if (similarTrackName + '|' + similarArtistName not in self.foundTracks):
					xbmc.PlayList(0).add(trackPath)
					#xbmc.executebuiltin( "AddToPlayList(" + trackPath + ";0)")
					self.countFoundTracks += 1
					self.foundTracks += [similarTrackName + '|' + similarArtistName]
			
			#uriPB.update(percentComplete, 'Finding similar tracks to: ' + currentlyPlayingTitle + " by: " + currentlyPlayingArtist, str(self.countFoundTracks) + " found so far - (try:" + str(self.currentSeedingTrack) + "/" + str(self.maxRetries) +")" )   
			uriPB.update(int(percentComplete), str(self.countFoundTracks) + " found so far - (try:" + str(self.currentSeedingTrack + 1) + "/" + str(self.maxRetries) +")" )   
			
		if (self.countFoundTracks < 25 and len(self.foundTracks) > self.currentSeedingTrack and self.currentSeedingTrack < self.maxRetries):
			print "TOO few results. Trying again with: " + self.foundTracks[self.currentSeedingTrack]
			similarTrackName =self.foundTracks[self.currentSeedingTrack].split('|')[0]
			similarArtistName =self.foundTracks[self.currentSeedingTrack].split('|')[1]
			self.currentSeedingTrack += 1
			self.fetch_similarTracks(similarTrackName,similarArtistName)
			uriPB.update(100, 'Taking you to your playlist...')

		if (self.countFoundTracks == 0 and self.currentSeedingTrack < self.maxRetries):
			uriPB.update(100, 'No results found...')
			time.sleep(3)
			return False
			
		uriPB.close()
		
		xbmc.executebuiltin('SetCurrentPlaylist(0)')
		xbmc.executebuiltin('XBMC.ActivateWindow(10500)')
	
if ( __name__ == "__main__" ):
    Main()
