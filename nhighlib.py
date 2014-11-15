# NHigh - version 2.0.1
# http://metanet.2.forumer.com/index.php?showtopic=6697
# Written by jg9000  (jg9000 at gmail.com)
#
# You may freely modify and distribute this program, as long
# as I am credited.

import urllib, cPickle, datetime, httplib, time, sys, os, re
import struct

NUM_EPISODES = 100
FRAMES_PER_SEC = 40
FRAME_TIME = 0.025



### The following is needed for python 2.3 support:   
if not hasattr(__builtins__,'set'):
    from sets import Set as set
def itemgetter(index): #same as operator.itemgetter
    return lambda x: x[index]
def sortList(lst, key=None, reverse=False):
    if sys.version_info >= (2,4):
        lst.sort(key=key, reverse=reverse)
    else:
        if key:
            lst2 = [(key(x),x) for x in lst]
            lst2.sort()
            lst[:] = [x[1] for x in lst2]
        else:
            lst.sort()
        if reverse:
            lst.reverse()
##################################################


####### config #######

class _ConfigField(object):
    def __init__(self, name, default, readFunc=str, writeFunc=str):
        self.name = name
        self.default = default
        self.readFunc = readFunc
        self.writeFunc = writeFunc

def _cfg_strToList(val):
    return val.split()
def _cfg_listToStr(val):
    return '  '.join(val)
class NHighConfig(object):
    def __init__(self):
        self.fields = [
            _ConfigField('defaultFilename', 'latest.hs'),
            _ConfigField('defaultPlayerName', self._getPlayerFromSol),
            _ConfigField('allowZerothTies', 1, readFunc=int),
            _ConfigField('ignoredPlayers', ['SEKular_proKRAStinator', 'JoE_DiZZle', '00danny1212', 'Haxxer', 'a_m_i_r_s', 'kryX-orange', 'eRaSeR_', 'Vuteur', '_________________', '\xa0\xa0\xa0\xa0', '\xa0\xa0\xa0\xa0\xa0', '\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0n\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0', '\xad\xa0\xa0\xa0\xa0\xa0\xa0\xa0', '\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0', '\x97\x97\x97\x97\x97\x97\x97\x97\x97\x97\x97\x97\x97\x97\x97\x97', 'jason_k'],
                         readFunc=_cfg_strToList, writeFunc=_cfg_listToStr),
            _ConfigField('nHighVersion', '2.0.1')
        ]
        self.fieldsDict = dict([(fld.name, fld) for fld in self.fields])
        self._findConfigFile()
        self.read()

    def read(self):
        for fld in self.fields:
            setattr(self, fld.name, fld.default)

        try:
            f=file(self.configFile,'r')
            fdata = f.read()
            f.close()
        except (IOError,OSError):
            fdata = ''

        for line in fdata.splitlines():
            sp = [x.strip() for x in line.split('=',1)]
            if len(sp)!=2: continue
            fldname, fldval = sp
            if fldname not in self.fieldsDict: continue
            fld = self.fieldsDict[fldname]
            try:
                fldval = fld.readFunc(fldval)
            except (TypeError, ValueError):
                continue
            setattr(self, fld.name, fldval)
            
        for fld in self.fields:
            val = getattr(self, fld.name)
            if hasattr(val, '__call__'):
                #it's a function that will retun the actual value.
                setattr(self, fld.name, val())

        self.onUpdated()
        if not os.path.exists(self.configFile):
            try:
                self.save()
            except (IOError, OSError):
                pass
        
    def save(self): #doesn't catch IOError
        self.onUpdated()
        if not os.path.exists(self.configDir):
            os.makedirs(self.configDir)
        f = file(self.configFile, 'w')
        try:
            f.write('''\
# * NHigh configuration file *
# This is an automatically generated file.

''')
            for fld in self.fields:
                fldval = getattr(self, fld.name)
                fldval = fld.writeFunc(fldval)
                f.write('%s = %s\n\n' % (fld.name, fldval))
        finally:
            f.close()

    def onUpdated(self):
        self.ignoredPlayersSet = set([x.lower() for x in self.ignoredPlayers])

    def _findConfigFile(self):
        self.configDir = findPreferencesDir('NHigh')
        if not self.configDir:
            self.configDir = os.curdir
        self.configFile = os.path.join(self.configDir, 'nhighconfig')
        return self.configFile

    def _getPlayerFromSol(self):
        '''When the config file didn't exist, get the default
        player name from the .sol file'''
        try:
            solData = readSolFile()
            val = unicode2str(solData['username'])
            if val=='anon': #uninitialized
                return 'jg9000'
            return val
        except (IOError, OSError, NHighError, TypeError, KeyError):
            return 'jg9000'

#####################

def unicode2str(u, errors='replace'):
    return u.encode('latin1', errors)

class NHighError(StandardError):
    pass

class AppURLopener(urllib.FancyURLopener):
    def __init__(self, *args):
        self.version = "NHigh/2.0"
        urllib.FancyURLopener.__init__(self, *args)
urllib._urlopener = AppURLopener()

def openURL(url, data=None):
    try:
        f = urllib.urlopen(url, data)
        ret = f.read()
        f.close()
        return ret
    except AttributeError: #workaround a urllib bug
        raise IOError('HTTP error: connection reset')
    except httplib.HTTPException,e:
        raise IOError, ('http error: '+str(e)), sys.exc_info()[2]

class HighScore(object):
    def __init__(self, name=None, score=None):
        self.name = name
        self.score = score
    def gettime(self):
        return self.score * FRAME_TIME
    time = property(gettime)
    def __str__(self):
        return '[%s, %0.3f]'%(self.name,self.time)
    def __repr__(self):
        return str(self)
    def __eq__(self, other):
        return hasattr(other,'name') and self.name==other.name and \
               hasattr(other,'score') and self.score==other.score
    def __ne__(self, other):
        return not self.__eq__(other)
    def __hash__(self):
        return hash((self.name, self.score))

class HSTable(object):
    def __init__(self, table=None, timestamp=None):
        if timestamp is None:
            timestamp = datetime.datetime.now().replace(microsecond=0)
        self.timestamp = timestamp
        self.table = table

emptyHighScore = HighScore('', 0)

def _postProcessLevelScores(lvlScores):
    for i in xrange(len(lvlScores)-1,-1,-1):
        entry = lvlScores[i]
        if entry.name.lower() in config.ignoredPlayersSet:
            del lvlScores[i]
            lvlScores.append(emptyHighScore)

def _downloadAllEpisodeScoresOnce(ep, ret):
    url = 'http://www.harveycartel.org/metanet/n/data13/get_topscores_query_jg.php'
    postdata = 'episode%5Fnumber=' + str(ep)
    try:
        data = openURL(url, postdata).replace('\r','').split('&')
    except IOError:
        return False
    dct = {}
    for assignment in data:
        if not assignment: continue
        sp = assignment.split('=',1)
        if len(sp)!=2: continue
        dct[sp[0]] = sp[1]
    for lvl in xrange(6):
        lvlkey = '01234e'[lvl]
        try:
            for rank in xrange(20):
                scorekey = lvlkey+'score'+str(rank)
                namekey = lvlkey+'name'+str(rank)
                score = int(dct[scorekey])
                name = dct[namekey].strip()
                ret[lvl][rank] = HighScore(name, score)
        except KeyError:
            return False
        except (TypeError,ValueError):
            raise NHighError('Bad data received')
        _postProcessLevelScores(ret[lvl])
    return True
    
def _downloadAllEpisodeScores(ep):
    ret = [[emptyHighScore]*20 for i in range(6)]
    #sometimes we get bad data from the server - so try again
    for trynum in xrange(5):
        if _downloadAllEpisodeScoresOnce(ep,ret):
            break
        time.sleep(5)
    else:
        raise NHighError('Error reading scores for episode %d'%ep)
    time.sleep(0.5)
    return ret

class HSDownloader(object):
    def __iter__(self):
        '''Generator that does a partial download and yields
        the amount done (0.0 to 1.0).'''
        self._table = []
        for ep in xrange(NUM_EPISODES):
            yield ep*1.0/NUM_EPISODES
            self._table.append(_downloadAllEpisodeScores(ep))
        yield 1.0
    def result(self):
        '''The resulting HSTable. Only call this when the iterator
        is finished.'''
        return HSTable(self._table)

    
def fixFileName(fname):
    if '.' not in fname:
        return fname + '.hs'
    return fname

#the pickled data is a tuple of:
#(format_ver (1), date/time, [100*[6*[20*(name, score)]]])

def saveScores(hsTable, fname):
    fname = fixFileName(fname)
    f=file(fname, 'wb')
    lst = [[[(entry.name, entry.score)
             for entry in lvl_entries]
             for lvl_entries in epi_entries]
             for epi_entries in hsTable.table]
    data = (1, hsTable.timestamp, lst)
    cPickle.dump(data, f, 2)
    f.close()

def loadScores(fname):
    try:
        fname = fixFileName(fname)
        f=file(fname, 'rb')
        data = cPickle.load(f)
        f.close()
        if data[0]!=1:
            raise NHighError("Bad file format")
        table = [[[HighScore(name,score)
                   for (name,score) in lvl_entries]
                   for lvl_entries in epi_entries]
                   for epi_entries in data[2]]
        for epi_entries in table:
            for lvl_entries in epi_entries:
                _postProcessLevelScores(lvl_entries)
        return HSTable(table, data[1])
    except (TypeError,ValueError):
        raise NHighError("Bad file format")

def getPlayerZeroth(hsTable, player):
    '''Find all 0th for a player.
    Return a list of tuples (episode, level, hs entry)'''
    pllower = player.lower()
    ret = []
    for ep_num, ep_entries in enumerate(hsTable.table):
        for lvl_num, lvl_entries in enumerate(ep_entries):
            numOf0th = _getNumOfZeroth(lvl_entries)
            for rank in xrange(numOf0th):
                entry = lvl_entries[rank]
                if entry.name.lower() == pllower:
                    ret.append((ep_num, lvl_num, entry))
    return ret

def getPlayerScores(hsTable, player):
    '''Find all highscores for a player.
    Return a list of tuples (episode, level, rank, hs entry)'''
    pllower = player.lower()
    return [(ep_num, lvl_num, rank, entry)
            for ep_num, ep_entries in enumerate(hsTable.table)
            for lvl_num, lvl_entries in enumerate(ep_entries)
            for rank, entry in enumerate(lvl_entries)
            if entry.name.lower()==pllower]

def findZerothImprovements(hsTableOld, hsTableNew):
    '''Find places where the 0th improved.
    Return list of tuples (episode, level, old entry, new entry)'''
    ret = []
    for episode in xrange(NUM_EPISODES):
        for level in range(6):
            oldZeroth = hsTableOld.table[episode][level][0]
            newZeroth = hsTableNew.table[episode][level][0]
            if oldZeroth.score != newZeroth.score:
                ret.append((episode, level, oldZeroth, newZeroth))
    return ret

def getLevelName(episode, level):
    if level==5:
        return '%02d'%episode
    else:
        return '%02d-%d'%(episode,level)

def getLevelRankDifferences(hsTable, rank1, rank2):
    '''calc differences between 2 different ranks for all levels.
      return sorted down list of tuples: (ep_num, lvl_num, diff, entry1, entry2)'''
    assert 0<=rank1<rank2<=19
    ret = []
    for ep_num, ep_entries in enumerate(hsTable.table):
        for lvl_num, lvl_entries in enumerate(ep_entries[:5]):
            #need to be careful because removing fake scores can result in empty entries
            rank1now = rank1
            rank2now = rank2
            while lvl_entries[rank2now]==emptyHighScore and rank2now>0:
                rank2now -= 1
            if rank1now > rank2now:
                rank1now = rank2now
            ret.append( (ep_num,lvl_num,
                         lvl_entries[rank1now].time-lvl_entries[rank2now].time,
                         lvl_entries[rank1now], lvl_entries[rank2now]) )
    
    sortList(ret, reverse=True, key=itemgetter(2))
    return ret

def _getNumOfZeroth(lvlEntries):
    'Return the number of tied 0th in a level given its entries'
    if not config.allowZerothTies:
        return 1
    zerothScore = lvlEntries[0].score
    for i,entry in enumerate(lvlEntries):
        if entry.score < zerothScore:
            return i
    return 20

def getAllPlayerStats(hsTable, includeEpisodes=True):
    '''returns a dict from lowercase player name
       to [player_name, num_zeroth, num_scores'''
    ret = {}
    def _getPlayerEntry(plyr):
        new_entry = [plyr,0,0]
        if not plyr: return new_entry #don't count empty scores
        return ret.setdefault(plyr.lower(), new_entry)
    for ep in hsTable.table:
        if not includeEpisodes:
            ep = ep[:5]
        for lvl in ep:
            num0th = _getNumOfZeroth(lvl)
            for rank, hsentry in enumerate(lvl):
                plentry = _getPlayerEntry(hsentry.name)
                if rank < num0th:
                    plentry[1] += 1
                plentry[2] += 1
    return ret


##### replay download/analysis #####

def getReplayKey(ep, lvl, rank):
    if ep<0 or ep>=NUM_EPISODES or lvl<0 or lvl>4 or rank<0 or rank>19:
        return None
    url = 'http://www.harveycartel.org/metanet/n/data13/get_topscores_query_jg.php'
    postdata = 'episode%5Fnumber=' + str(ep)
    allscores = openURL(url, postdata).replace('\r','')
    searchstr = r'&%dpkey%d=(\d+)' % (lvl, rank)
    m=re.search(searchstr, allscores)
    if not m:
        return None
    return int(m.group(1))

def downloadReplayByPKey(pkey):
    url = 'http://www.harveycartel.org/metanet/n/data13/get_lv_demo.php'
    postdata = 'pk='+str(pkey)
    return openURL(url, postdata).replace('\r','')

def downloadReplay(ep, lvl, rank):
    'Returns tuple: (player,score,demo)'
    try:
        pkey = getReplayKey(ep, lvl, rank)
        if pkey is None:
            raise NHighError('Unable to download replay - replay key not found')

        alldata = downloadReplayByPKey(pkey)
        m_name=re.search('&name=([^&]+)',alldata)
        m_score=re.search('&score=([^&]+)',alldata)
        m_demo=re.search('&demo=([^&]+)',alldata)
        try:
            player = m_name.group(1)
            demo = m_demo.group(1)
            score = int(m_score.group(1))
        except (ValueError, AttributeError):
            raise NHighError('Unable to download replay - received invalid data')

        return (player, score, demo)        
        
    except IOError:
        raise NHighError('Error downloading replay data')

def getReplayKeyName(key):
    ret = ''
    if key&1: ret += 'L'
    if key&2: ret += 'R'
    if key&4: ret += 'J'
    if key==0: ret = 'Nothing'
    return ret

def parseReplay(data):
    '''Parse the replay and return array of numbers (1 per frame).
    The numbers can be passed to getReplayKeyName.'''

    if data and data[0]=='$':
        #skip level data
        m = re.match(r'^\$[^#]*#[^#]*#[^#]*#[^#]*#([^#]*)',data)
        if not m:
            raise NHighError('Invalid demo data')
        data = m.group(1)

    m=re.match(r'^(\d+):((\d+\|)*\d+)$', data)
    if not m:
        raise NHighError('Invalid demo data')
    frames = int(m.group(1))
    keystring = m.group(2)
    nums = [int(x) for x in re.findall(r'\d+',keystring)]
    ret = []
    for num in nums:
        numbits = min(frames, 7)
        for bit in xrange(numbits):
            ret.append(num & 0xF)
            num >>= 4
            
        frames -= numbits
        if frames==0 and num!=0:
            #framecount is lower than number of provided frames
            return ret
    return ret

    
def parseAndCompactReplay(data):
    '''Parse the replay, and then find sequences of unchanged keys.
    Return array of tuples (frame_num, key_num, # of occurences)
    The key numbers can be passed to getReplayKeyName.'''

    ret = []
    keys=parseReplay(data)
    if not keys:
        return ret
    keys.append(-1)
    lastkey=-1
    count=0
    frame=0
    for key in keys:
        key = key&7
        if key==lastkey:
            count+=1
        else:
            if lastkey!=-1:
                ret.append((frame-count, lastkey, count))
            lastkey = key
            count = 1
        frame += 1
    return ret

########

def getPlatform():
    for plat in ['win','darwin','linux','mac']:
        if sys.platform.startswith(plat):
            return plat
    return sys.platform

def findPreferencesDir(appname):
    """
    Typical app preference directories are:
        Windows:    C:\Documents and Settings\<username>\Application Data\<owner>\<appname>
        Mac OS X:   ~/Library/Preferences/<appname>
        Unix:       ~/.<lowercased-appname>
    """
    platform = getPlatform()
    if platform=='win':
        try:
            path = os.environ['appdata']
            path = os.path.join(path, appname)
        except KeyError:
            path = None
    elif platform == 'darwin' or platform == 'mac':
        try:
            from Carbon import Folder, Folders
            path = Folder.FSFindFolder(Folders.kUserDomain,
                                       Folders.kPreferencesFolderType,
                                       Folders.kDontCreateFolder)
            path = os.path.join(path.FSRefMakePath(), appname)
        except ImportError:
            path = os.path.expanduser("~/Library/Preferences/"+appname)
    else:
        path = os.path.expanduser("~/." + appname.lower())
    return path


##### .sol handling #####

def findSolFile():
    platform = getPlatform()
    if platform in ['win','darwin','mac']:
        macromediaDir = findPreferencesDir('Macromedia')
        if not macromediaDir:
            return None
        soBaseDir = os.path.join(macromediaDir, 'Flash Player', '#SharedObjects')
        if not os.path.isdir(soBaseDir):
            #I'm not sure if this version actually exists - metanet FAQ mentions it for Mac OS 9
            soBaseDir = os.path.join(macromediaDir, 'Flash Player', '#Shared Objects')
            if not os.path.isdir(soBaseDir):
                return None
        soFiles = [os.path.join(soBaseDir, x) for x in os.listdir(soBaseDir)]
        soDirs = [x for x in soFiles if os.path.isdir(x)]
        if not soDirs:
            return None
        soDir = soDirs[0]
    else: #linux/unix/etc
        soDir = os.path.expanduser('~/.macromedia/Macromedia/Flash Player')

    solFile = os.path.join(soDir, 'localhost', 'n_v14b_userdata.sol')
    if not os.path.exists(solFile):
        return None
    return solFile


class SolReader(object):
    def __init__(self):
        self.readFuncs ={
            0: self.readNumber,
            1: self.readBool,
            2: self.readStr,
            3: self.readObj,
            5: self.readNull,
            6: self.readUndef,
            8: self.readArray,
            #10: self.readRawArr,
            #11: self.readDate,
            #13: self.readObjM,
            #15: self.readObjXML,
            #16: self.readCustomClass,
        }

    def readFromFile(self, size):
        ret = self.f.read(size)
        if len(ret) < size:
            raise EOFError()
        return ret
        
    def readStr(self):
        length, = struct.unpack('>H',self.readFromFile(2))
        if length==0:
            return ''
        s = self.readFromFile(length)
        return s.decode('utf-8')

    def readSol(self, f):
        ret = {}
        try:
            self.f = f
            self.readFromFile(2) #header?
            datasize, = struct.unpack('>L',self.readFromFile(4)) #datasize == filesize-6
            self.readFromFile(4) #filetype=='TCSO' ?
            self.readFromFile(6) #??
            self.readStr() #the .sol name == n_v14b_userdata
            self.readFromFile(4) #??

            while True:
                name = self.readStr()
                val = self.readValue()
                ret[name] = val
                self.readFromFile(1) # == 0
        except EOFError:
            pass
        except (ValueError, TypeError, struct.error):
            raise NHighError('.sol file contains invalid format')
        return ret

    def readNumber(self):
        val, = struct.unpack('>d', self.readFromFile(8))
        return val

    def readBool(self):
        return bool(ord(self.readFromFile(1)))

    def readObj(self):
        ret = {}
        while True:
            name = self.readStr()
            if not name: break
            val = self.readValue()
            ret[name] = val
        self.readFromFile(1) # ==9
        return ret

    def readArray(self):
        length, = struct.unpack('>L',self.readFromFile(4))
        last = -1
        ret = []
        while True:
            name = self.readStr()
            if not name: break
            try:
                now = int(name)
            except ValueError:
                raise NHighError('.sol File contains invalid array object')
            if now != last+1:
                raise NHighError('.sol File contains invalid array object')
            last = now
            ret.append(self.readValue())
        if last != length-1:
            raise NHighError('.sol File contains invalid array object')
        self.readFromFile(1) # ==9
        return ret

    def readNull(self):
        return None

    def readUndef(self):
        return None

    def readValue(self):
        typ = ord(self.readFromFile(1))
        func = self.readFuncs.get(typ)
        if func:
            return func()
        else:
            raise NHighError('.sol File contains unrecognized objects')


def readSolFile():
    filename = findSolFile()
    if not filename:
        raise NHighError('.sol file not found')
    try:
        f = file(filename, 'rb')
        try:
            return SolReader().readSol(f)
        finally:
            f.close()
    except (IOError,OSError):
        raise NHighError('Error reading .sol file')

##############


def calcTotalScores(solData):
    totalEpisodeScore = 0
    totalLevelScore = 0
    try:
        for ep in xrange(NUM_EPISODES):
            epData = solData['persBest'][ep]
            totalEpisodeScore += int(epData['ep']['score'])
            for lvl in xrange(5):
                totalLevelScore += int(epData['lev'][lvl]['score'])
    except (KeyError,TypeError):
        raise NHighError('.sol data is incomplete')
    return (totalLevelScore, totalEpisodeScore)

def findUnsubmittedTop20(solData, hsTable):
    '''Returns: (player, results)
    where results is a list of tuples (ep_num, lvl_num, rank, unsubmitted_score, old_rank, old_entry)
    '''
    ret = []
    player = unicode2str(solData['username'])
    pllower = player.lower()
    try:
        for ep in xrange(NUM_EPISODES):
            epSolData = solData['persBest'][ep]
            solScores = [0]*6
            for lvl in xrange(5):
                solScores[lvl] = int(epSolData['lev'][lvl]['score'])
            solScores[5] = int(epSolData['ep']['score'])
            
            epHSData = hsTable.table[ep]
            for lvl in xrange(6):
                solScore = solScores[lvl]
                lvlHSData = epHSData[lvl]
                for rank,entry in enumerate(lvlHSData):
                    if entry.score == 0:
                        break
                    if entry.score < solScore:
                        oldEntry = None
                        oldRank = None
                        for r, en in enumerate(lvlHSData):
                            if en.name.lower() == pllower:
                                oldEntry = en
                                oldRank = r
                                break
                        ret.append((ep, lvl, rank, solScore, oldRank, oldEntry))
                        break
                    if entry.name.lower() == pllower:
                        break
        return (player, ret)
    except (KeyError,TypeError):
        raise NHighError('.sol data is incomplete')
    

config = NHighConfig()

if __name__=='__main__':
    print 'Do not run this file - run nhigh.py instead'
    raw_input('Press Enter...')
