# -*- coding: utf-8 -*-

""" TV Portuguesa
    2014 fightnight"""

import xbmc, xbmcgui, xbmcaddon, xbmcplugin,re,sys, urllib, urllib2,time,datetime,os,requests,json,htmlentitydefs

versao = '0.5.0'
user_agent = 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'
tvporpath = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')).decode('utf-8')
pastaperfil = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile')).decode('utf-8')
order=['RTP1','RTP2','SIC','TVI','RTPINF','SICN','TVI24','EURON','RTPACO','RTPAFR','RTPINT','RTPMAD','RTPMEM','ARTV','ETV','TPA','FASH','TRACE','DJING','VIRGIN']

RadiosURL = 'http://www.radios.pt/portalradio/'
PATH = "XBMC_TVPOR"
UATRACK="UA-39199007-1"

def canais():
    GA("None","listacanais")
    if xbmcaddon.Addon().getSetting("programacao") == "true": programas=p_todos()
    else: programas=[]
    if xbmcaddon.Addon().getSetting("radios") == "true": addDir("[B][COLOR white]Radios[/COLOR][/B]",'nada',2,os.path.join(tvporpath,'resources','art','thumb_radios.png'),1,'Oiça comodamente radios nacionais.',True)
    if xbmcaddon.Addon().getSetting("praias") == "true": addDir("[B][COLOR white]Praias[/COLOR][/B]",'nada',5,os.path.join(tvporpath,'resources','art','thumb_info.png'),1,'Webcams das melhores praias nacionais.',True)
    lcanais=channellist()
    for idcanal in order:
        addCanal("[B]%s[/B] %s" % (lcanais[idcanal]['name'].encode('utf-8'),p_umcanal(programas,lcanais[idcanal]['epg'],'nomeprog')),'nada',idcanal,os.path.join(tvporpath,'resources','art',lcanais[idcanal]['thumb']),len(order),p_umcanal(programas,lcanais[idcanal]['epg'],'descprog'))
    xbmcplugin.setContent(int(sys.argv[1]), 'livetv')

def channellist():
    return json.loads(openfile('lib.json',pastafinal=os.path.join(tvporpath,'resources')))

def request_servidores(chid,auto=False):
    try:
        headers = {'User-Agent': user_agent}
        listacanais=channellist()
        if len(listacanais[chid]['streams']) > 0:
            titulos=[]; ligacao=[]; resolve=[]
            
            for individual in listacanais[chid]['streams']:
                if 'www.rtp.pt' in individual['url']:
                    import base64
                    conteudo=abrir_url(individual['url'])
                    try:
                        linksmil=re.compile('"smil":"(.+?)"').findall(conteudo)[0]
                        if not linksmil.startswith('http://'): linksmil=base64.b64decode(linksmil)
                        titulos.append('%s (SMIL)' % (individual['name']))
                        ligacao.append(linksmil)
                        resolve.append(False)
                    except: pass
                    
                    try:
                        link=re.compile('"d":"(.+?)"').findall(conteudo)[0]
                        if link!=linksmil:
                            if not link.startswith('http://'): link=base64.b64decode(link)
                            titulos.append('%s (M3U8)' % (individual['name']))
                            ligacao.append(link)
                            resolve.append(False)
                    except: pass

                    try:
                        streamer=re.compile('"streamer": "(.+?)"').findall(conteudo)[0]
                        app=re.compile('"application": "(.+?)"').findall(conteudo)[0]
                        filep=re.compile('"file": "(.+?)"').findall(conteudo)[0]
                        link='rtmp://%s/%s playPath=%s swfUrl=http://programas.rtp.pt/play/player.swf?v3 swfVfy=1 live=1 pageUrl=%s' % (streamer,app,filep,individual['url'])
                        titulos.append('%s (RTMP)' % (individual['name']))
                        ligacao.append(link)
                        resolve.append(False)
                    except: pass

                elif 'videos.sapo.pt' in individual['url']:
                    conteudo=requests.get('%s/mov/24?all=1' % (individual['url']), headers=headers)
                    flag=False
                    if conteudo.status_code == 200: flag=True
                    else:
                        conteudo=requests.get('%s/mov/24?all=1' % (individual['url']).replace('http://','http://rd3.'), headers=headers)
                        if conteudo.status_code == 200: flag=True

                    if flag==True:
                        try:
                            link=re.compile('"hls":"(.+?)"').findall(conteudo.text)[0].replace('\\','')
                            titulos.append('%s (M3U8)' % (individual['name']))
                            ligacao.append(link)
                            resolve.append(False)
                        except: pass

                        try:
                            link=re.compile('"rtmp":"(.+?)"').findall(conteudo.text)[0].replace('\\','')
                            titulos.append('%s (RTMP)' % (individual['name']))
                            ligacao.append('%s swfUrl=http://js.sapo.pt/Projects/Video/150129_PATCHED_R2/flash/videojs.swf swfVfy=1 live=1 pageUrl=%s' % (link,individual['url']))
                            resolve.append(False)
                        except: pass

                        try:
                            link=re.compile('"rtsp":"(.+?)"').findall(conteudo.text)[0].replace('\\','')
                            titulos.append('%s (RTSP)' % (individual['name']))
                            ligacao.append(link)
                            resolve.append(False)
                        except: pass
                
                else:    
                    titulos.append(individual['name'])
                    ligacao.append(individual['url'])
                    resolve.append(individual['resolve'])
            if len(ligacao)==1: index=0
            else:
                if auto==True or xbmcaddon.Addon().getSetting("automatico") == "true":
                    from random import randint
                    index =randint(0, len(ligacao)-1)
                else: index = xbmcgui.Dialog().select('Escolha o servidor', titulos)

            if index > -1:
                if resolve[index]==True:
                    resolvers(ligacao[index],chid)
                else:
                    playvideo(ligacao[index],chid)
            
        else:
            xbmcgui.Dialog().ok("TV Portuguesa","Nenhum stream disponível.")
    except Exception:
        xbmcgui.Dialog().ok("TV Portuguesa","Erro a obter servidores.")
        (etype, value, traceback) = sys.exc_info()
        print "%s\n%s\n%s" % (etype,value,traceback)


def resolvers(p_end,chid=None,name=None):
    try:
        m3u8_url=None
        headers = {'User-Agent': user_agent}
        conteudo = requests.get(p_end, headers=headers).text
        if 'dailymotion.com' in conteudo and 'dailymotion.com' in p_end:
            if re.search('stream_live_hls_url',conteudo):
                temp=re.compile('"stream_live_hls_url":"(.+?)"').findall(conteudo)[0].replace('\\','')
                m3u8_url=redirect(temp)

        elif '<jwplayer:streamer>' in conteudo:
            rtmp=re.compile('<jwplayer:streamer>(.+?)</jwplayer:streamer>').findall(conteudo)[0]
            try: filelocation=re.compile('<media:content bitrate=".+?" url="(.+?)" width=".+?"').findall(conteudo)[0]
            except:
                filelocation= re.compile('<media:content url="(.+?)"').findall(conteudo)[0]
                if 'TPAI.mp4' in filelocation: p_end='http://muntumedia.com/television/10-tpai'
            m3u8_url='%s playPath=%s swfUrl=http://www.tpai.tv/swf/jwplayer/player.swf live=true pageUrl=%s' % (rtmp,filelocation,p_end)

        elif 'euronews.com' in conteudo:
            datac= {'action':'getHexaglobeUrl'}
            r = requests.post(p_end, data=datac,headers=headers)
            headers = {'User-Agent': user_agent,'Referer':p_end}
            r = requests.get(r.text, headers=headers)
            if re.search('"status":"ok"',r.text):
                m3u8_url=re.compile('"pt":{"hls":"(.+?)"').findall(r.text)[0].replace('\\','')

        elif 'tviplayer.iol.pt' in conteudo:
            m3u8_url=re.compile("videoUrl: '(.+?)'").findall(conteudo)[0]

        elif 'surftotal' in conteudo:
            try:
                try:m3u8_url=re.compile("""<source src="([^"]+?)" type='rtmp/mp4'>""").findall(conteudo)[0]
                except:m3u8_url=re.compile('<source src="([^"]+?)" type="application/x-mpegURL">').findall(conteudo)[0]
            except:                
                pass

        elif 'surfline' in conteudo:
            idcam=re.compile('spotid = (.+?),').findall(conteudo)[0]            
            streaminfo=abrir_url('http://api.surfline.com/v1/syndication/cam/%s' % (idcam)).replace('\\','')
            if re.search('"camStatus":"down"',streaminfo): pass
            else: m3u8_url=re.compile('"file":"(.+?)"').findall(streaminfo)[0]

        elif 'videos.sapo.pt' in conteudo:
            try:
                videoid=re.compile('http://videos.sapo.pt/(.+?)&').findall(conteudo)[0]
                streamlist=abrir_url('http://videos.sapo.pt/%s?all=1' % (videoid))
            except:
                embed=re.compile('file=(.+?)&').findall(conteudo)[0]
                streamlist=abrir_url('%s?all=1' % (embed))
            m3u8_url=re.compile('"hls":"(.+?)"').findall(streamlist)[0].replace('\\','')

        if m3u8_url: playvideo(m3u8_url,chid=chid,name=name)
        else: print "Nada disponivel"

    except Exception:
        xbmcgui.Dialog().ok("TV Portuguesa","Servidor não suportado.")
        (etype, value, traceback) = sys.exc_info()
        print "%s\n%s\n%s" % (etype,value,traceback)

def radio_resolver(chid,nacional=True):
    stream_url=None
    rname=None
    thumb=None
    if nacional==True:
        headers = {'User-Agent': user_agent}
        urlrequest='http://www.radioonline.com.pt/ajax/player.php?clear_s_name=%s' % (chid)
        link=clean(abrir_url(urlrequest))
        thumb=re.compile('id="station-logo-player" src="(.+?)" alt=".+?"').findall(link)[0]
        rname=re.compile('id="station-logo-player" src=".+?" alt="(.+?)"').findall(link)[0].replace('Radio ','')
        try: player=re.compile('soundManager.createSound\({(.+?)autoLoad').findall(link)[0]
        except: player=False
        try:
            print player
            endereco=re.compile('url: "(.+?)"').findall(player)[0].replace(';','')
            if re.search('serverURL',player):
                rtmp=re.compile('serverURL: "(.+?)"').findall(player)[0]
                rtmp=rtmp.replace(':1936','') #tempfix
                stream_url=rtmp + endereco
            else: stream_url=endereco
        except:pass
        
        if not stream_url:
            try:stream_url=re.compile('<param name="URL" value="(.+?)"').findall(link)[0]
            except:
                try: stream_url=re.compile('<object data="(.+?)"').findall(link)[0]
                except: pass

    else:
        headers = {'User-Agent': user_agent,'Referer':'http://www.radios.pt/portalradio/homepage.htm'}
        urlrequest='http://www.radios.pt/portalradio/Sintonizador/?radio_id=%s&scope=0' % (chid)
        r = requests.get(urlrequest, headers=headers)
        stream_url=re.compile('<param name="url" value="(.+?)"').findall(r.text)[0]
        thumb='http://www.radio.com.pt/APR.ROLI.WEB/Images/Logos/'+ chid +'.gif'
        rname=re.compile('<span id="lblNomeRadio">(.+?)</span>').findall(r.text)[0]

    if stream_url: playmusic(stream_url,rname=rname,thumb=thumb)
    else: print "Nada disponivel"
        

def playvideo(linkfinal,chid=None,name=None):
    if chid==None:
        if name==None: name='Nome indisponível'
        thumb=os.path.join(tvporpath,'resources','art','thumb_info.png')
    else:
        listacanais=channellist()
        name='[B]%s[/B]' % (listacanais[chid]['name'])
        thumb=os.path.join(tvporpath,'resources','art',listacanais[chid]['thumb'])

    GA("player",chid)
    listitem = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=thumb)
    playlist = xbmc.PlayList(1)
    playlist.clear()
    listitem.setInfo("Video", {"Title":name,"overlay":6,"playcount":0})
    listitem.setProperty('IsPlayable', 'true')
    playlist.add(linkfinal, listitem)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]),True,listitem)
    if int(sys.argv[1]) < 0:
        xbmc.Player().play(playlist,listitem)

def playmusic(linkfinal,rname=None,thumb=None):
    if rname==None: rname='Sem Nome'
    if thumb==None: thumb=''
    listitem = xbmcgui.ListItem(rname, iconImage="DefaultVideo.png", thumbnailImage=thumb,path=linkfinal)
    listitem.setInfo("Music", {"Title":rname})
    listitem.setProperty('IsPlayable', 'true')
    playlist = xbmc.PlayList(1)
    playlist.clear()
    playlist.add(linkfinal, listitem)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]),True,listitem)
    if int(sys.argv[1]) < 0:
        xbmc.Player().play(playlist,listitem)

def praias():
    BeachcamURL = 'http://beachcam.sapo.pt/'
    SurflineURL= 'http://www.surfline.com'
    SurftotalURL='http://www.surftotal.com'
    beachcams=[]
    try:
        temp=abrir_url(BeachcamURL + 'pt/livecams/')
        beachcams=re.compile('<a href="/pt/livecams/(.+?)">(.+?)</a>').findall(temp)    
    except: print "Nao foi possivel obter as BeachCams"
    try:
        temp=abrir_url(SurflineURL + '/surf-report/portugal_2946/map/')
        beachcams+=re.compile('\tbackground-image:url./surfdata/images/icon_hdcam_blue.gif.\n\t\t\t\t\n                ;background-repeat:no-repeat;background-position:bottom left"\n                href="(.+?)">(.+?)</a>').findall(temp)
    except: print "Nao foi possivel obter as Surfline"
    try:
        temp=re.compile('Report<b class="caret">(.+?)</li></ul></li>').findall(abrir_url(SurftotalURL))[0]
        beachcams+=re.compile('<a href="(.+?)" >(.+?)</a>').findall(temp)
    except: print "Nao foi possivel obter as Surftotal"
    beachcams.sort(key=lambda t: t[1])
    import base64
    for end,nome in beachcams:
        nome=nome.replace('&#227;','ã').replace('&#231;','ç').replace('&#237;','í').replace('&#180;','á')
        if re.search('surf-report',end):
            end=SurflineURL + end
            nome= '[B]%s[/B] (Surfline)' % nome
        elif re.search('camaras-report',end):
            end=SurftotalURL + end
            nome= '[B]%s[/B] (Surftotal)' % nome
        else:
            end=BeachcamURL + 'pt/livecams/' + end
            nome= '[B]%s[/B] (Beachcam.pt)' % nome
        
        addCanal(nome,end,end,os.path.join(tvporpath,'resources','art','thumb_info.png'),len(beachcams),'',resolve=True)
        #addDir(nome,end,7,,'',False)
    
def p_todos():
    if xbmcaddon.Addon().getSetting("programacao") == "false": return ''
    else:
        try:
            dia=horaportuguesa(True)
            listacanais='RTP1,RTP2,SIC,TVI,RTPIN,SICN,TVI24,FASH,RTPAC,RTPA,RTPM,RTPMD,ETVHD,TPA,ARTV,TRACE,EURN'
            url='http://services.sapo.pt/EPG/GetChannelListByDateInterval?channelSiglas='+listacanais+'&startDate=' + dia +':01&endDate='+ dia + ':02'
            link=clean(abrir_url(url,erro=False))
            
            listas=re.compile('<Sigla>(.+?)</Sigla>.+?<Title>(.+?)</Title>.+?<Description>(.+?)</Description>').findall(link)
            canais={}
            for nomecanal, nomeprog, descricao in listas:
                canais[nomecanal]={'nomeprog':'(' + nomeprog + ')','descprog':descricao}
            return canais
        except: pass

def p_umcanal(listas,desejado,desc):
    try:
        if desejado==None: return ''
        else: return listas[desejado][desc]
    except: return ''

def programacao_canal():
    listacanais=channellist()
    dia=horaportuguesa(True)
    diaseguinte=horaportuguesa('diaseguinte')
    url='http://services.sapo.pt/EPG/GetChannelListByDateIntervalJson?channelSiglas='+listacanais[name]['epg']+'&startDate=' + dia +':01&endDate='+ diaseguinte + ':02'
    ref=int(0)
    link=abrir_url(url)
    titles=['[B][COLOR white]Programação:[/COLOR][/B]']

    programas=re.compile('{"Actor":.+?"Description":"(.+?)".+?"StartTime":".+?-.+?-(.+?) (.+?):(.+?):.+?".+?"Title":"(.+?)"').findall(link)
    for descprog,dia, horas,minutos, nomeprog in programas:
        ref=ref+1
        if dia==datetime.datetime.now().strftime('%d'): dia='Hoje'
        else: dia='Amanhã'
        titles.append('\n[B][COLOR blue]%s %s:%s[/COLOR][/B] - [B][COLOR gold]%s[/COLOR][/B] - %s' % (dia,horas,minutos,nomeprog,descprog))
    programacao='\n'.join(titles)
    
    try:
        xbmc.executebuiltin("ActivateWindow(10147)")
        window = xbmcgui.Window(10147)
        xbmc.sleep(100)
        window.getControl(1).setLabel('TV Portuguesa - %s' % (listacanais[name]['name'].encode('utf-8')))
        window.getControl(5).setText(programacao)
    except: pass

### RADIOS ####

def radios():
    addDir('[COLOR blue][B]Radios Locais[/B][/COLOR]','nada',3,os.path.join(tvporpath,'resources','art','thumb_radios.png'),1,'',True)
    link=clean(abrir_url('http://www.radioonline.com.pt'))
    nacionais=re.compile('<div class="radiostation boxgrid">(.+?)</div>').findall(link)
    for radioindividual in nacionais:
        radiosnacionais=re.compile('<a href="http://www.radioonline.com.pt/#(.+?)".+?<img.+?src="(.+?)".+?alt="(.+?)"').findall(radioindividual)
        for idradio,imagemradio,nomeradio in radiosnacionais:
            addRadio(nomeradio.replace('Radio ',''),idradio,imagemradio,len(radiosnacionais),'',nacional=True)

def radioslocais():
    link=clean(abrir_url(RadiosURL))
    distritos=re.compile('id="DirectorioPesquisa1_ddlDistritos">(.+?)</select>').findall(link)[0]
    distritos=distritos.replace('<option value="0"></option>','<option value="0">Todos as rádios locais</option>')
    lista=re.compile('<option value="(.+?)">(.+?)</option>').findall(distritos)
    for iddistrito,nomedistrito in lista:
        addDir(nomedistrito,RadiosURL + '?distrito=' + iddistrito + '&concelho=0&tipo=0',4,os.path.join(tvporpath,'resources','art','thumb_radios.png'),len(lista),'',True)
    xbmc.executebuiltin("Container.SetViewMode(501)")

def listar_radios(name,url):
    link=clean(abrir_url(url))
    radios=re.compile('<td><a href="/portalradio/conteudos/ficha/.+?radio_id=(.+?)">(.+?)</a></td><td>(.+?)</td>.+?<td align="center">').findall(link)
    for idradio,nomeradio,concelho in radios:
        addRadio('[B]'+nomeradio+'[/B] ('+concelho+')',idradio,'http://www.radio.com.pt/APR.ROLI.WEB/Images/Logos/'+ idradio +'.gif',len(radios),'',nacional=False)
    try:
        pagina=re.compile('<div id="DirectorioPesquisa1_divPageSelector">.+?<b> (.+?)</b>  <a href=/portalradio/(.+?)>').findall(link)[0]
        nrpag=int(pagina[0])+1
        nrpag=str(nrpag)
        addDir('[COLOR blue]Próxima página (' + nrpag + ') >>>[/COLOR]',RadiosURL + pagina[1],4,os.path.join(tvporpath,'resources','art','thumb_radios.png'),1,'',True)
    except: pass
    xbmc.executebuiltin("Container.SetViewMode(501)")

def abrir_url(url,erro=True):
    try:
        print "A fazer request normal de: " + url
        req = urllib2.Request(url)
        req.add_header('User-Agent', user_agent)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        return link
    except urllib2.HTTPError, e:
        host='http://' + url.split('/')[2]
        xbmcgui.Dialog().ok('TV Portuguesa',str(urllib2.HTTPError(e.url, e.code, "Erro na página.", e.hdrs, e.fp)),'Verifique manualmente se a página está operacional.',host)
        sys.exit(0)
    except urllib2.URLError, e:
        xbmcgui.Dialog().ok('TV Portuguesa',"Erro na página. Verifique manualmente",'se a página está operacional. ' + url)
        sys.exit(0)

def openfile(filename,pastafinal=pastaperfil):
    try:
        destination = os.path.join(pastafinal, filename)
        fh = open(destination, 'rb')
        contents=fh.read()
        fh.close()
        return contents
    except:
        print "Nao abriu os temporarios de: %s" % filename
        return None

def checker():
    if xbmcaddon.Addon().getSetting('ga_visitor')=='':
        from random import randint
        xbmcaddon.Addon().setSetting('ga_visitor',str(randint(0, 0x7fffffff)))
    checkGA()

def clean(text):
    command={'\r':'','\n':'','\t':'','&nbsp;':'','&#231;':'ç','&#201;':'É','&#233;':'é','&#250;':'ú','&#227;':'ã','&#237;':'í','&#243;':'ó','&#193;':'Á','&#205;':'Í','&#244;':'ô','&#224;':'à','&#225;':'á','&#234;':'ê','&#211;':'Ó','&#226;':'â'}
    regex = re.compile("|".join(map(re.escape, command.keys())))
    return regex.sub(lambda mo: command[mo.group(0)], text)

def redirect(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', user_agent)
    response = urllib2.urlopen(req)
    gurl=response.geturl()
    return gurl

def horaportuguesa(sapo):
    if sapo==True or sapo=='diaseguinte': fmt = '%Y-%m-%d%%20%H:%M'
    else: fmt = '%Y-%m-%d %H-%M-%S'

    if xbmcaddon.Addon().getSetting('horaportuguesa') == 'true':
        dt  = datetime.datetime.now()
        if sapo=='diaseguinte':
            dts = dt.strftime('%Y-%m-') + str(int(dt.strftime('%d')) + 1) +dt.strftime('%%20%H:%M')
            #special dia seguinte case
        else: dts = dt.strftime(fmt)
        return dts
    else:
        import pytz
        dt  = datetime.datetime.now()
        timezona= xbmcaddon.Addon().getSetting('timezone2')
        terradamaquina=str(pytz.timezone(pytz.all_timezones[int(timezona)]))
        if sapo=='diaseguinte': dia=int(dt.strftime('%d')) + 1
        else: dia=int(dt.strftime('%d'))
        d = pytz.timezone(terradamaquina).localize(datetime.datetime(int(dt.strftime('%Y')), int(dt.strftime('%m')), dia, hour=int(dt.strftime('%H')), minute=int(dt.strftime('%M'))))
        lisboa=pytz.timezone('Europe/Lisbon')
        convertido=d.astimezone(lisboa)

        dts=convertido.strftime(fmt)
        return dts

def descape(content):
      content = re.sub('&([^;]+);', lambda m: unichr(htmlentitydefs.name2codepoint[m.group(1)]), content)
      return content.encode('utf-8')

def parseDate(dateString):
    try: return datetime.datetime.fromtimestamp(time.mktime(time.strptime(dateString.encode('utf-8', 'replace'), "%Y-%m-%d %H:%M:%S")))
    except: return datetime.datetime.today() - datetime.timedelta(days = 1) #force update

def checkGA():
    secsInHour = 60 * 60
    threshold  = 2 * secsInHour
    now   = datetime.datetime.today()
    prev  = parseDate(xbmcaddon.Addon().getSetting('ga_time'))
    delta = now - prev
    nDays = delta.days
    nSecs = delta.seconds
    doUpdate = (nDays > 0) or (nSecs > threshold)
    if not doUpdate: return
    xbmcaddon.Addon().setSetting('ga_time', str(now).split('.')[0])
    APP_LAUNCH()    
    
                    
def send_request_to_google_analytics(utm_url):
    try:
        req = urllib2.Request(utm_url, None,{'User-Agent':user_agent})
        response = urllib2.urlopen(req).read()
    except:
        print ("GA fail: %s" % utm_url)         
    return response
       
def GA(group,name):
        try:
            try:
                from hashlib import md5
            except:
                from md5 import md5
            from random import randint
            import time
            from urllib import unquote, quote
            from os import environ
            from hashlib import sha1
            VISITOR = xbmcaddon.Addon().getSetting('ga_visitor')
            utm_gif_location = "http://www.google-analytics.com/__utm.gif"
            if not group=="None":
                    utm_track = utm_gif_location + "?" + \
                            "utmwv=" + versao + \
                            "&utmn=" + str(randint(0, 0x7fffffff)) + \
                            "&utmt=" + "event" + \
                            "&utme="+ quote("5("+PATH+"*"+group+"*"+name+")")+\
                            "&utmp=" + quote(PATH) + \
                            "&utmac=" + UATRACK + \
                            "&utmcc=__utma=%s" % ".".join(["1", VISITOR, VISITOR, VISITOR,VISITOR,"2"])
                    try:
                        print "============================ POSTING TRACK EVENT ============================"
                        send_request_to_google_analytics(utm_track)
                    except:
                        print "============================  CANNOT POST TRACK EVENT ============================" 
            if name=="None":
                    utm_url = utm_gif_location + "?" + \
                            "utmwv=" + versao + \
                            "&utmn=" + str(randint(0, 0x7fffffff)) + \
                            "&utmp=" + quote(PATH) + \
                            "&utmac=" + UATRACK + \
                            "&utmcc=__utma=%s" % ".".join(["1", VISITOR, VISITOR, VISITOR, VISITOR,"2"])
            else:
                if group=="None":
                       utm_url = utm_gif_location + "?" + \
                                "utmwv=" + versao + \
                                "&utmn=" + str(randint(0, 0x7fffffff)) + \
                                "&utmp=" + quote(PATH+"/"+name) + \
                                "&utmac=" + UATRACK + \
                                "&utmcc=__utma=%s" % ".".join(["1", VISITOR, VISITOR, VISITOR, VISITOR,"2"])
                else:
                       utm_url = utm_gif_location + "?" + \
                                "utmwv=" + versao + \
                                "&utmn=" + str(randint(0, 0x7fffffff)) + \
                                "&utmp=" + quote(PATH+"/"+group+"/"+name) + \
                                "&utmac=" + UATRACK + \
                                "&utmcc=__utma=%s" % ".".join(["1", VISITOR, VISITOR, VISITOR, VISITOR,"2"])
                                
            print "============================ POSTING ANALYTICS ============================"
            send_request_to_google_analytics(utm_url)
            
        except:
            print "================  CANNOT POST TO ANALYTICS  ================" 
            
            
def APP_LAUNCH():
        versionNumber = int(xbmc.getInfoLabel("System.BuildVersion" )[0:2])
        print versionNumber
        if versionNumber < 12:
            if xbmc.getCondVisibility('system.platform.osx'):
                if xbmc.getCondVisibility('system.platform.atv2'):
                    log_path = '/var/mobile/Library/Preferences'
                else:
                    log_path = os.path.join(os.path.expanduser('~'), 'Library/Logs')
            elif xbmc.getCondVisibility('system.platform.ios'):
                log_path = '/var/mobile/Library/Preferences'
            elif xbmc.getCondVisibility('system.platform.windows'):
                log_path = xbmc.translatePath('special://home')
                log = os.path.join(log_path, 'xbmc.log')
                logfile = open(log, 'r').read()
            elif xbmc.getCondVisibility('system.platform.linux'):
                log_path = xbmc.translatePath('special://home/temp')
            else:
                log_path = xbmc.translatePath('special://logpath')
            log = os.path.join(log_path, 'xbmc.log')
            logfile = open(log, 'r').read()
            match=re.compile('Starting XBMC \((.+?) Git:.+?Platform: (.+?)\. Built.+?').findall(logfile)
        elif versionNumber > 11:
            print '======================= more than ===================='
            if versionNumber < 14: filename='xbmc.log'
            else: filename='kodi.log'
            log_path = xbmc.translatePath('special://logpath')
            log = os.path.join(log_path, filename)
            logfile = open(log, 'r').read()
            if versionNumber < 14: match=re.compile('Starting XBMC \((.+?) Git:.+?Platform: (.+?)\. Built.+?').findall(logfile)
            else: match=re.compile('Starting Kodi \((.+?) Git:.+?Platform: (.+?)\. Built.+?').findall(logfile)
        else:
            logfile='Starting XBMC (Unknown Git:.+?Platform: Unknown. Built.+?'
            match=re.compile('Starting XBMC \((.+?) Git:.+?Platform: (.+?)\. Built.+?').findall(logfile)
        print '==========================   '+PATH+' '+versao+'  =========================='
        try:
            from hashlib import md5
        except:
            from md5 import md5
        from random import randint
        import time
        from urllib import unquote, quote
        from os import environ
        from hashlib import sha1
        import platform
        VISITOR = xbmcaddon.Addon().getSetting('ga_visitor')
        for build, PLATFORM in match:
            if re.search('12',build[0:2],re.IGNORECASE): 
                build="Frodo" 
            if re.search('11',build[0:2],re.IGNORECASE): 
                build="Eden" 
            if re.search('13',build[0:2],re.IGNORECASE): 
                build="Gotham" 
            print build
            print PLATFORM
            utm_gif_location = "http://www.google-analytics.com/__utm.gif"
            utm_track = utm_gif_location + "?" + \
                    "utmwv=" + versao + \
                    "&utmn=" + str(randint(0, 0x7fffffff)) + \
                    "&utmt=" + "event" + \
                    "&utme="+ quote("5(APP LAUNCH*"+build+"*"+PLATFORM+")")+\
                    "&utmp=" + quote(PATH) + \
                    "&utmac=" + UATRACK + \
                    "&utmcc=__utma=%s" % ".".join(["1", VISITOR, VISITOR, VISITOR,VISITOR,"2"])
            try:
                print "============================ POSTING APP LAUNCH TRACK EVENT ============================"
                send_request_to_google_analytics(utm_track)
            except:
                print "============================  CANNOT POST APP LAUNCH TRACK EVENT ============================" 

def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'): params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2: param[splitparams[0]]=splitparams[1]                         
    return param



def addCanal(name,url,chid,iconimage,total,descricao,resolve=False,mode=0):
    cm=[]
    if resolve: u="%sresolve/?name=%s&url=%s" % (sys.argv[0],name,urllib.quote_plus(url))
    else: u="%splay/%s" % (sys.argv[0],chid)
    liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name,"overlay":6,"playcount":0} )
    liz.setProperty('fanart_image', "%s/fanart.jpg"%xbmcaddon.Addon().getAddonInfo("path"))
    liz.setProperty('IsPlayable', 'true')
    cm.append(('Ver programação', "XBMC.RunPlugin(%s?mode=%s&name=%s)"%(sys.argv[0],6,chid)))
    liz.addContextMenuItems(cm, replaceItems=False)
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False,totalItems=total)

def addRadio(name,chid,iconimage,total,descricao,nacional=True,mode=0):
    cm=[]
    if nacional: u="%sradio/nacional/%s" % (sys.argv[0],chid)
    else: u="%sradio/local/%s" % (sys.argv[0],chid)
    liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo( type="Music", infoLabels={ "Title": name,"playcount":0} )
    liz.setProperty('fanart_image', "%s/fanart.jpg"%xbmcaddon.Addon().getAddonInfo("path"))
    liz.setProperty('IsPlayable', 'true')
    liz.addContextMenuItems(cm, replaceItems=False)
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False,totalItems=total)

def addDir(name,url,mode,iconimage,total,descricao,pasta):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
    liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name, "overlay":6 ,"plot":descricao} )
    liz.setProperty('fanart_image', "%s/fanart.jpg"%xbmcaddon.Addon().getAddonInfo("path"))
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=pasta,totalItems=total)

params=get_params()
url=None
thumb=None
name=None
mode=None

try: url=urllib.unquote_plus(params["url"])
except: pass
try: thumb=urllib.unquote_plus(params["thumb"])
except: pass
try: name=urllib.unquote_plus(params["name"])
except: pass
try: mode=int(params["mode"])
except: pass

checker()

if '/play/' in sys.argv[0]:
    try:status=sys.argv[0].split('&auto=')[1]
    except: status='False'
    if status=='True': request_servidores(sys.argv[0].split('/play/')[1].split('&auto=')[0],auto=True)
    else: request_servidores(sys.argv[0].split('/play/')[1])

elif '/external/' in sys.argv[0]:
    playvideo(url,name=name)

elif '/resolve/' in sys.argv[0]:
    resolvers(url,name=name)

elif '/radio/' in sys.argv[0]:
    if '/nacional/' in sys.argv[0]: radio_resolver(sys.argv[0].split('/nacional/')[1],nacional=True)
    else: radio_resolver(sys.argv[0].split('/local/')[1],nacional=False)
    
elif mode==None:
    print "Versao Instalada: v" + versao
    if xbmcaddon.Addon().getSetting('termos') == 'true':
        mensagemaviso()
        xbmcaddon.Addon().setSetting('termos',value='false')
    canais()

elif mode==1: menu_principal()
elif mode==2: radios()
elif mode==3: radioslocais()
elif mode==4: listar_radios(name,url)
elif mode==5: praias()
elif mode==6: programacao_canal()
        
xbmcplugin.endOfDirectory(int(sys.argv[1]))
