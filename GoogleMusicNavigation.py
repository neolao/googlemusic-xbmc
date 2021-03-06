import xbmc, xbmcplugin, utils
import GoogleMusicApi
import time
from urllib import unquote_plus, urlencode
from xbmcgui import ListItem

class GoogleMusicNavigation():
    def __init__(self):
        self.lang    = utils.addon.getLocalizedString
        self.fanart  = utils.addon.getAddonInfo('fanart')
        self.api     = GoogleMusicApi.GoogleMusicApi()

        self.main_menu_aa = (
            {'title':self.lang(30211), 'params':{'path':"ifl"}},
            {'title':self.lang(30219), 'params':{'path':"listennow"}},
            {'title':self.lang(30220), 'params':{'path':"topcharts"}},
            {'title':self.lang(30221), 'params':{'path':"newreleases"}},
            {'title':self.lang(30209), 'params':{'path':"library"}},
            {'title':self.lang(30222), 'params':{'path':"browse_stations"}},
            {'title':self.lang(30204), 'params':{'path':"playlists", 'playlist_type':"auto"}},
            {'title':self.lang(30202), 'params':{'path':"playlists", 'playlist_type':"user"}},
            {'title':self.lang(30208), 'params':{'path':"search"}}
        )
        self.main_menu_noaa = (
            {'title':self.lang(30211), 'params':{'path':"ifl"}},
            {'title':self.lang(30209), 'params':{'path':"library"}},
            {'title':self.lang(30204), 'params':{'path':"playlists", 'playlist_type':"auto"}},
            {'title':self.lang(30202), 'params':{'path':"playlists", 'playlist_type':"user"}},
            {'title':self.lang(30208), 'params':{'path':"search"}}
        )
        self.lib_menu = (
            {'title':self.lang(30203), 'params':{'path':"playlists",'playlist_type':"radio"}},
            {'title':self.lang(30210), 'params':{'path':"playlist", 'playlist_id':"feellucky"}},
            {'title':self.lang(30214), 'params':{'path':"playlist", 'playlist_id':"shuffled_albums"}},
            {'title':self.lang(30201), 'params':{'path':"playlist", 'playlist_id':"all_songs"}},
            {'title':self.lang(30205), 'params':{'path':"filter", 'criteria':"artist"}},
            {'title':self.lang(30206), 'params':{'path':"filter", 'criteria':"album"}},
            {'title':self.lang(30207), 'params':{'path':"filter", 'criteria':"genre"}},
            {'title':self.lang(30212), 'params':{'path':"filter", 'criteria':"composer"}},
        )

    def listMenu(self, params={}):
        get   = params.get
        path  = get("path", "root")
        utils.log("PATH: "+path)

        listItems = []
        view_mode_id = ''
        content = ''
        sortMethods = [xbmcplugin.SORT_METHOD_UNSORTED]

        if path == "root":
            if eval(utils.addon.getSetting('all-access')):
                listItems = self.getMenuItems(self.main_menu_aa)
            else:
                utils.log("NO ALL ACCESS/UNLIMITED ACCOUNT")
                listItems = self.getMenuItems(self.main_menu_noaa)

        elif path == "ifl":
            listItems = self.addSongsFromLibrary(self.api.getStationTracks("IFL"), 'library')
            content = "songs"

        elif path == "library":
            listItems = self.getMenuItems(self.lib_menu)

        elif path == "playlist":
            listItems = self.listPlaylistSongs(get("playlist_id"))
            if get("playlist_id")=='all_songs':
                sortMethods = [xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE]
            content = "songs"

        elif path == "station":
            listItems = self.addSongsFromLibrary(self.api.getStationTracks(get('id')), 'library')
            content = "songs"

        elif path == "playlists":
            listItems = self.getPlaylists(get('playlist_type'))
            view_mode_id = utils.addon.getSetting('playlists_viewid')

        elif path == "filter" and 'album' == get('criteria'):
            listItems = self.listAlbums(get('criteria'))
            sortMethods = [xbmcplugin.SORT_METHOD_ALBUM_IGNORE_THE, xbmcplugin.SORT_METHOD_VIDEO_YEAR,
                           xbmcplugin.SORT_METHOD_ARTIST, xbmcplugin.SORT_METHOD_ALBUM, xbmcplugin.SORT_METHOD_DATE]
            content = "albums"

        elif path in ["artist", "genre"] and get('name'):
            album_name = unquote_plus(get('name'))
            listItems = self.listAlbums(path, album_name)
            paramsAllSongs = {'path':"allcriteriasongs",'criteria':path,'name':album_name}
            listItems.insert(0,self.createFolder('* '+self.lang(30201), paramsAllSongs))
            sortMethods = [xbmcplugin.SORT_METHOD_ALBUM_IGNORE_THE, xbmcplugin.SORT_METHOD_VIDEO_YEAR,
                           xbmcplugin.SORT_METHOD_ARTIST, xbmcplugin.SORT_METHOD_ALBUM, xbmcplugin.SORT_METHOD_DATE]
            content = "albums"

        elif path == "filter":
            listItems = self.getCriteria(get('criteria'))
            sortMethods = [xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE]

        elif path == "allcriteriasongs":
            listItems = self.listAllCriteriaSongs(get('criteria'), get('name'))
            sortMethods = [xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE]
            content = "songs"

        elif path in ["genre", "artist", "album", "composer"]:
            songs = self.api.getFilterSongs(path, unquote_plus(get('album')), unquote_plus(get('artist','')))
            listItems = self.addSongsFromLibrary(songs, 'library')
            sortMethods = [xbmcplugin.SORT_METHOD_TRACKNUM,  xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE,
                           xbmcplugin.SORT_METHOD_PLAYCOUNT, xbmcplugin.SORT_METHOD_SONG_RATING]
            content = "songs"

        elif path == "search":
            keyboard = xbmc.Keyboard('', self.lang(30208))
            keyboard.doModal()
            if keyboard.isConfirmed() and keyboard.getText():
                listItems = self.getSearch(keyboard.getText())
            else: return
            content = "songs"

        elif path == "search_result":
            utils.log("SEARCH_RESULT: "+get('query'))
            listItems = self.getSearch(params)
            content = "songs"

        elif path == "listennow":
            listItems = self.getListennow(self.api.getApi().get_listen_now())
            content = "albums"

        elif path == "topcharts":
            listItems.append(self.createFolder(self.lang(30206),{'path':'topcharts_albums'}))
            listItems.append(self.createFolder(self.lang(30213),{'path':'topcharts_songs'}))

        elif path == "topcharts_songs":
            listItems = self.addSongsFromLibrary(self.api.getTopcharts(), 'library')
            content = "songs"

        elif path == "topcharts_albums":
            listItems = self.createAlbumFolder(self.api.getTopcharts(content_type='albums'))
            content = "albums"

        elif path == "newreleases":
            listItems = self.createAlbumFolder(self.api.getNewreleases())
            content = "albums"

        elif path == "browse_stations":
            listItems = self.browseStations(get('category'))

        elif path == "get_stations":
            listItems = self.getStations(get('subcategory'))
            view_mode_id = utils.addon.getSetting('stations_viewid')

        elif path == "create_station":
            station = self.api.getApi().create_station(unquote_plus(get('name')), artist_id=get('artistid'), genre_id=get('genreid'), curated_station_id=get('curatedid'))
            listItems = self.addSongsFromLibrary(self.api.getStationTracks(station), 'library')
            content = "songs"

        elif path == "genres":
            listItems = self.getGenres(self.api.getApi().get_top_chart_genres())

        elif path == "store_album":
            utils.log("ALBUM: "+get('albumid'))
            listItems = self.addSongsFromLibrary(self.api.getAlbum(get('albumid')), 'library')
            content = "songs"

        elif path == "artist_topsongs":
            listItems = self.addSongsFromLibrary(self.api.getArtist(get('artistid')), 'library')
            content = "songs"

        elif path == "related_artists":
            listItems = []
            items = self.api.getArtist(get('artistid'), relartists=10)
            for item in items:
                params = {'path':'artist_topsongs', 'artistid':item['artistId']}
                artist_art = item['artistArtRef'] if 'artistArtRef' in item else utils.addon.getAddonInfo('icon')
                listItems.append(self.createFolder(item['name'], params, arturl=artist_art))

        else:
            utils.log("Invalid path: " + get("path"))
            return

        utils.setDirectory(listItems, content, sortMethods, view_mode_id)


    def getMenuItems(self, items):
        ''' Build the plugin root menu. '''
        menuItems = []
        for menu_item in items:
            params = menu_item['params']
            cm = []
            if 'playlist_id' in params:
                cm = self.getPlayAllContextMenuItems(menu_item['title'], params['playlist_id'])
            elif 'playlist_type' in params:
                cm = self.getPlaylistsContextMenuItems(menu_item['title'], params['playlist_type'])
            elif params['path'] == 'library':
                cm.append((self.lang(30314), "XBMC.RunPlugin(%s?action=export_library)" % utils.addon_url))
                cm.append((self.lang(30305), "XBMC.RunPlugin(%s?action=update_library)" % utils.addon_url))
                cm.append((self.lang(30306), "XBMC.RunPlugin(%s?action=add_favourite&path=library&title=%s)" % (utils.addon_url,menu_item['title'])))
            elif 'criteria' in params:
                cm.append((self.lang(30306), "XBMC.RunPlugin(%s?action=add_favourite&path=filter&criteria=%s&title=%s)" % (utils.addon_url,params['criteria'],menu_item['title'])))
            menuItems.append(self.createFolder(menu_item['title'], params, cm))
        return menuItems

    def listPlaylistSongs(self, playlist_id):
        utils.log("Loading playlist: " + playlist_id)
        songs = self.api.getPlaylistSongs(playlist_id)
        if playlist_id in ('thumbsup','lastadded','mostplayed','freepurchased','feellucky','all_songs','shuffled_albums'):
            return self.addSongsFromLibrary(songs, 'library')
        return self.addSongsFromLibrary(songs, 'playlist'+playlist_id)

    def addSongsFromLibrary(self, library, song_type):
        listItems = []
        append = listItems.append
        createItem = self.createItem

        for song in library:
            append([utils.getUrl(song), createItem(song, song_type)])

        return listItems

    def listAllCriteriaSongs(self, filter_type, filter_criteria):
        songs = self.api.getFilterSongs(filter_type, unquote_plus(filter_criteria), '')
        listItems = []
        append = listItems.append
        createItem = self.createItem

        # add album name when showing all artist songs
        for song in songs:
            songItem = createItem(song, 'library')
            songItem.setLabel("".join(['[',song['album'],'] ',song['title']]))
            songItem.setLabel2(song['album'])
            append([utils.getUrl(song), songItem])

        return listItems

    def getPlaylists(self, playlist_type):
        utils.log("Getting playlists of type: " + playlist_type)
        listItems = []
        append = listItems.append
        addFolder = self.createFolder

        if playlist_type == 'radio':
            icon = utils.addon.getAddonInfo('icon')
            for rs in self.api.getStations():
                #utils.log(repr(rs))
                image = rs['compositeArtRefs'][0]['url'] if 'compositeArtRefs' in rs else rs['imageUrls'][0]['url'] if 'imageUrls' in rs else icon
                cm = self.getRadioContextMenuItems(rs['name'], rs['id'])
                append(addFolder(rs['name'], {'path':"station",'id':rs['id']}, cm, image))

        elif playlist_type == 'auto':
            icon = utils.addon.getAddonInfo('icon')
            auto = [['thumbsup',self.lang(30215),icon],['lastadded',self.lang(30216),icon],
                    ['freepurchased',self.lang(30217),icon],['mostplayed',self.lang(30218),icon]]
            for pl_id, pl_name, pl_arturl in auto:
                cm = self.getPlayAllContextMenuItems(pl_name, pl_id)
                append(addFolder(pl_name, {'path':"playlist", 'playlist_id':pl_id}, cm, pl_arturl))

        else:
            for pl_id, pl_name, pl_arturl in self.api.getPlaylistsByType(playlist_type):
                cm = self.getPlayAllContextMenuItems(pl_name, pl_id)
                append(addFolder(pl_name, {'path':"playlist", 'playlist_id':pl_id}, cm, pl_arturl))

        return listItems

    def listAlbums(self, criteria, name=''):
        utils.log("LISTALBUMS: "+repr(criteria)+" "+repr(name))
        listItems = []
        append = listItems.append
        addFolder = self.createFolder
        getCm = self.getFilterContextMenuItems
        items = self.api.getCriteria(criteria, name)

        #utils.log(repr(items))
        for item in items:
            #utils.log(repr(item))
            album  = item['album']
            artist = item['album_artist']
            params = {'path':criteria,'album':album,'artist':artist}
            folder = addFolder(album, params, getCm(criteria, album), item['arturl'], artist)
            folder[1].setInfo(type='music', infoLabels={
                   'year':item['year'], 'artist':artist, 'album':album,
                   'date':time.strftime('%d.%m.%Y', time.gmtime(item['date']/1000000))})
            append(folder)

        return listItems

    def getCriteria(self, criteria):
        utils.log("CRITERIA: "+repr(criteria))
        listItems = []
        append = listItems.append
        addFolder = self.createFolder
        getCm = self.getFilterContextMenuItems
        items = self.api.getCriteria(criteria)

        if criteria in ('artist','genre'):
            for item in items:
                append( addFolder(item['criteria'], {'path':criteria,'name':item['criteria']}, getCm(criteria, item['criteria']), item['arturl']))

        else:
            for item in items:
                append( addFolder(item['criteria'], {'path':criteria,'album':item['criteria']}, getCm(criteria, item['criteria'])))

        return listItems

    def getListennow(self, items):
        listItems = []

        for item in items:
            suggestion = item.get('suggestion_text')
            image = item['images'][0]['url'] if 'images' in item else None
            if item['type'] == '1':
                album = item['album']
                listItems.extend(self.createAlbumFolder([{
                    'name'        :album['title']+' ('+suggestion+')',
                    'artist'      :album['artist_name'],
                    'albumArtRef' :image,
                    'albumId'     :album['id']['metajamCompactKey']}]))

            elif item['type'] == '3':
                radio  = item['radio_station']
                params = {'path':'create_station', 'name':utils.tryEncode('Radio %s (%s)'%(radio['title'], suggestion))}
                seed   = radio['id']['seeds'][0]
                if seed['seedType'] == '3':
                    params['artistid'] = seed['artistId']
                elif seed['seedType'] == '5':
                    params['genreid'] = seed['genreId']
                else: utils.log("ERROR seedtype unknown "+repr(seed['seedType']))
                listItems.append(self.createFolder(params['name'], params, arturl=image))

            else: utils.log("ERROR item type unknown "+repr(item['type']))

        return listItems

    def browseStations(self, index=None):
        listItems = []
        items = self.api.getApi().get_station_categories()
        #utils.log("INDEX:"+repr(index)+"\n"+repr(items))
        if index:
            # list subcategories from category index
            items = items[int(index)]['subcategories']
            params = {'path':'get_stations'}
        else:
            # list stations categories
            params = {'path':'browse_stations'}
        for item in items:
            # populate with categories or subcategories
            params['category'] = items.index(item)
            params['subcategory'] = item['id']
            listItems.append(self.createFolder(item['display_name'], params))
        return listItems

    def getStations(self, stationId):
        listItems = []
        items = self.api.getApi().get_stations(stationId)
        for item in items:
            params = {'path':'create_station','curatedid':item['seed']['curatedStationId'], 'name':utils.tryEncode(item['name'])}
            listItems.append(self.createFolder(item['name'], params, arturl=item['compositeArtRefs'][0]['url']))
        return listItems

    def getGenres(self, items):
        listItems = []
        print repr(items)
        return listItems

    def createAlbumFolder(self, items):
        listItems = []
        for item in items:
            params = {'path':'store_album', 'albumid':item['albumId']}
            cm = [(self.lang(30301), "XBMC.RunPlugin(%s?action=play_all&album_id=%s)" % (utils.addon_url, item['albumId'])),
                  (self.lang(30309), "XBMC.RunPlugin(%s?action=add_album_library&album_id=%s)" % (utils.addon_url, item['albumId'])),
                  (self.lang(30315) or 'Add to queue', "XBMC.RunPlugin(%s?action=add_to_queue&album_id=%s)" % (utils.addon_url, item['albumId']))]
            listItems.append(self.createFolder("[%s] %s"%(item['artist'], item['name']), params, cm, item['albumArtRef']))
        #print repr(items)
        return listItems

    def createFolder(self, name, params, contextMenu=[], arturl='', name2='*'):
        li = ListItem(label=name, label2=name2, thumbnailImage=arturl)
        li.addContextMenuItems(contextMenu, replaceItems=True)
        li.setProperty('fanart_image', self.fanart)
        return "?".join([utils.addon_url, urlencode(params)]), li, "true"

    def createItem(self, song, song_type):
        infoLabels = {
            'tracknumber': song['tracknumber'], 'duration':   song['duration'],
            'year':        song['year'],        'genre':      song['genre'],
            'album':       song['album'],       'artist':     song['artist'],
            'title':       song['title'],       'playcount':  song['playcount'],
            'rating':      song['rating'],      'discnumber': song['discnumber']
        }

        li = utils.createItem(song['display_name'], song['albumart'])
        li.setProperty('fanart_image', song['artistart'])
        li.setInfo(type='music', infoLabels=infoLabels)
        li.addContextMenuItems(self.getSongContextMenu(song['song_id'], song['display_name'], song_type))
        return li

    def getSongContextMenu(self, song_id, title, song_type):
        cm = []
        if song_id.startswith('T'):
            cm.append((self.lang(30309), "XBMC.RunPlugin(%s?action=add_library&song_id=%s)" % (utils.addon_url,song_id)))
            cm.append((self.lang(30319) or 'Artist top songs', "XBMC.RunPlugin(%s?action=artist_topsongs&song_id=%s)" % (utils.addon_url,song_id)))
            cm.append((self.lang(30320) or 'Related artists', "XBMC.RunPlugin(%s?action=related_artists&song_id=%s)" % (utils.addon_url,song_id)))
        if song_type == 'library':
            cm.append((self.lang(30307),"XBMC.RunPlugin(%s?action=add_playlist&song_id=%s)" % (utils.addon_url,song_id)))
        elif song_type.startswith('playlist'):
            cm.append((self.lang(30308), "XBMC.RunPlugin(%s?action=del_from_playlist&song_id=%s&playlist_id=%s)" % (utils.addon_url, song_id, song_type[8:])))
        cm.append((self.lang(30409) or "Rating", "XBMC.RunPlugin(%s?action=set_thumbs&song_id=%s)" % (utils.addon_url, song_id)))
        cm.append((self.lang(30313), "XBMC.RunPlugin(%s?action=play_yt&title=%s)" % (utils.addon_url, title)))
        cm.append((self.lang(30311), "XBMC.RunPlugin(%s?action=search_yt&title=%s)" % (utils.addon_url, title)))
        cm.append((self.lang(30310), "XBMC.RunPlugin(%s?action=start_radio&song_id=%s)" % (utils.addon_url,song_id)))
        return cm

    def getRadioContextMenuItems(self, name, radio_id):
        cm = []
        cm.append((self.lang(30301), "XBMC.RunPlugin(%s?action=play_all&radio_id=%s)" % (utils.addon_url, radio_id)))
        cm.append((self.lang(30302), "XBMC.RunPlugin(%s?action=play_all&radio_id=%s&shuffle=true)" % (utils.addon_url, radio_id)))
        cm.append((self.lang(30312), "XBMC.RunPlugin(%s?action=play_all_yt&radio_id=%s)" % (utils.addon_url, radio_id)))
        cm.append((self.lang(30306), "XBMC.RunPlugin(%s?action=add_favourite&path=playlist&radio_id=%s&title=%s)" % (utils.addon_url, radio_id, name)))
        cm.append((self.lang(30315) or 'Add to queue', "XBMC.RunPlugin(%s?action=add_to_queue&radio_id=%s)" % (utils.addon_url, radio_id)))
        cm.append((self.lang(30318) or 'Delete station', "XBMC.RunPlugin(%s?action=delete_station&radio_id=%s&title=%s)" % (utils.addon_url, radio_id, name)))
        return cm

    def getPlayAllContextMenuItems(self, name, playlist):
        cm = []
        cm.append((self.lang(30301), "XBMC.RunPlugin(%s?action=play_all&playlist_id=%s)" % (utils.addon_url, playlist)))
        cm.append((self.lang(30302), "XBMC.RunPlugin(%s?action=play_all&playlist_id=%s&shuffle=true)" % (utils.addon_url, playlist)))
        cm.append((self.lang(30312), "XBMC.RunPlugin(%s?action=play_all_yt&playlist_id=%s)" % (utils.addon_url, playlist)))
        cm.append((self.lang(30306), "XBMC.RunPlugin(%s?action=add_favourite&path=playlist&playlist_id=%s&title=%s)" % (utils.addon_url, playlist, name)))
        cm.append((self.lang(30314), "XBMC.RunPlugin(%s?action=export_playlist&playlist_id=%s&title=%s)" % (utils.addon_url, playlist, name)))
        cm.append((self.lang(30315) or 'Add to queue', "XBMC.RunPlugin(%s?action=add_to_queue&playlist_id=%s)" % (utils.addon_url, playlist)))
        cm.append((self.lang(30317) or 'Delete playlist', "XBMC.RunPlugin(%s?action=delete_playlist&playlist_id=%s&title=%s)" % (utils.addon_url, playlist, name)))
        return cm

    def getFilterContextMenuItems(self, filter_type, filter_criteria):
        cm = []
        cm.append((self.lang(30306), "XBMC.RunPlugin(%s?action=add_favourite&path=%s&name=%s&title=%s)" % (utils.addon_url, filter_type, filter_criteria, filter_criteria)))
        cm.append((self.lang(30301), "XBMC.RunPlugin(%s?action=play_all&filter_type=%s&filter_criteria=%s)" % (utils.addon_url, filter_type, filter_criteria)))
        cm.append((self.lang(30302), "XBMC.RunPlugin(%s?action=play_all&filter_type=%s&filter_criteria=%s&shuffle=true)" % (utils.addon_url, filter_type, filter_criteria)))
        cm.append((self.lang(30312), "XBMC.RunPlugin(%s?action=play_all_yt&filter_type=%s&filter_criteria=%s)" % (utils.addon_url, filter_type, filter_criteria)))
        cm.append((self.lang(30208), "XBMC.RunPlugin(%s?action=search&filter_type=%s&filter_criteria=%s)" % (utils.addon_url, filter_type, filter_criteria)))
        cm.append((self.lang(30315) or 'Add to queue', "XBMC.RunPlugin(%s?action=add_to_queue&filter_type=album&filter_criteria=%s)" % (utils.addon_url, filter_criteria)))
        return cm

    def getPlaylistsContextMenuItems(self, name, playlist_type):
        cm = []
        cm.append((self.lang(30304), "XBMC.RunPlugin(%s?action=update_playlists&playlist_type=%s)" % (utils.addon_url, playlist_type)))
        cm.append((self.lang(30306), "XBMC.RunPlugin(%s?action=add_favourite&path=playlists&playlist_type=%s&title=%s)" % (utils.addon_url, playlist_type, name)))
        cm.append((self.lang(30316) or 'Create playlist', "XBMC.RunPlugin(%s?action=create_playlist)" % utils.addon_url))
        return cm

    def getSearch(self, query):
        listItems = []

        def listAlbumsResults():
            listItems.append(self.createFolder('[COLOR orange]*** '+self.lang(30206)+' ***[/COLOR]',{'path':'none'}))
            for album in result['albums']:
                if 'albumId' in album:
                    listItems.extend(self.createAlbumFolder([album]))
                else:
                    params = {'path':"search_result",'query':utils.tryEncode(album['name'])}
                    listItems.append(self.createFolder("[%s] %s"%(album['artist'], album['name']), params, [], album['albumArtRef']))

        if isinstance(query,basestring):
            result = self.api.getSearch(query)
            if result['albums']: listAlbumsResults()
            if result['artists']:
                listItems.append(self.createFolder('[COLOR orange]*** '+self.lang(30205)+' ***[/COLOR]',{'path':'none'}))
                cm = []
                for artist in result['artists']:
                    params = {'path':"search_result",'query':utils.tryEncode(artist['name'])}
                    if 'artistId' in artist:
                        cm = [(self.lang(30301), "XBMC.RunPlugin(%s?action=play_all&artist_id=%s)" % (utils.addon_url, artist['artistId']))]
                        params['artistid'] = artist['artistId']
                    listItems.append(self.createFolder(artist['name'], params, cm, artist['artistArtRef'] if 'artistArtRef' in artist else ''))
            if result['tracks']:
                listItems.append(self.createFolder('[COLOR orange]*** '+self.lang(30213)+' ***[/COLOR]',{'path':'none'}))
                listItems.extend(self.addSongsFromLibrary(result['tracks'], 'library'))

        elif 'artistid' in query:
            result = self.api.getSearch(unquote_plus(query['query']))
            if result['albums']: listAlbumsResults()
            listItems.append(self.createFolder('[COLOR orange]*** '+self.lang(30213)+' ***[/COLOR]',{'path':'none'}))
            listItems.extend(self.addSongsFromLibrary(self.api.getArtist(query['artistid']), 'library'))

        else:
            #listItems.extend(self.addSongsFromLibrary(self.api.getSearch(unquote_plus(query['query']))['tracks'], 'library'))
            listItems.extend(self.getSearch(unquote_plus(query['query'])))

        return listItems



