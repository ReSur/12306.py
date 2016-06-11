# -*- coding:utf-8 -*-

import ssl, urllib2, json, time, datetime, os, sys, re

def analyseArguments(arguments, sets0, sets1, sets2, sets_infinity):
    if len(arguments) <= 1:
        return
    opts = []
    count = 0
    sets = sets0 + sets1 + sets2 + sets_infinity
    for keyword in arguments[1:]:
        if keyword in sets:
            if keyword in sets_infinity:
                count = -1
            elif keyword in sets1:
                count = 1
            elif keyword in sets2:
                count = 2
            else:
                count = 0
            opts.append([keyword, []])
        elif not opts or not count:
            opts.append(['empty', [keyword]])
            count = -1
        else:
            opts[-1][1].append(keyword)
            if count > 0:
                count-=1
    return opts
def refreshStations():
    pattern = re.compile('@(\w{3})\|(\W+)\|(\w{3})\|(\w+)\|(\w+)\|\d+', re.S)
    result = urllib2.urlopen('https://kyfw.12306.cn/otn/resources/js/framework/station_name.js', context=context, timeout = 10).read()
    return re.findall(pattern, result)
def selectStation(keyword, stations, msg = ''):
    select_station = []
    for station in stations:
        if keyword in (station[4], station[1], station[3]):
            select_station.append(station)
    if select_station:
        if len(select_station) == 1:
            return select_station[0]
        else:
            count = 1;
            for station in select_station:
                print '%d. %s' % (count, station[1])
                count+=1
            select = int(raw_input(u'请输入%s序号并回车: ' % msg))
            return select_station[select - 1]
    else:
        return selectStation(raw_input(u'未找到车站，请重新输入: '), stations, msg)
if __name__ == "__main__":
    context = ssl._create_unverified_context()
    train_date = datetime.date.today()
    from_station = ['hzh', '杭州', 'HZH', 'hangzhou', 'hz']
    to_station = ['jhu', '金华', 'JBH', 'jinhua', 'jh']
    train_type = ['D', 'G']
    start_time = 0
    arrive_time = 0
    opts = analyseArguments(sys.argv, ['-h', '--help'], ['-d', '--day', '-st', '--starttime', '-at', '--arrivetime'], ['-s', '--station'], ['-t', '-type'])
    if opts:
        for opt, vals in opts:
            if opt in ('-d', '--day'):
                date_format = re.match('((?<!\d)\d{1,2})\D(\d{1,2}(?!\d))', vals[0].decode('utf-8'))
                if date_format:
                    month = int(date_format.group(1))
                    if month < train_date.month:
                        year = train_date.year + 1
                    else:
                        year = train_date.year
                    train_date = datetime.date(year, month, int(date_format.group(2)))
                else:
                    try:
                        train_date+=datetime.timedelta(days=int(vals[0]))
                    except:
                        print u'间隔天数/出发日期 格式错误，默认使用今天'
            if opt in ('-s', '--station'):
                stations = refreshStations()
                if len(vals) == 1:
                    to_station = selectStation(vals[0], stations, u'［到达车站］的')
                else:
                    from_station = selectStation(vals[0], stations, u'［出发车站］的')
                    to_station = selectStation(vals[1], stations, u'［到达车站］的')
            if opt in ('-st', '--starttime'):
                start_time = int(vals[0])
            if opt in ('-at', '--arrivetime'):
                arrive_time = int(vals[0])
            if opt in ('-t', '--type'):
                vals
                for i in range(len(vals)):
                    vals[i] = vals[i].upper()
                train_type = set(vals)
            if opt in ('-h', '--help'):
                print u'usage: python 12306.py\n\t[-d/--day 间隔天数/出发日期（*月*日）]\n\t[-s/--station [出发车站] 到达车站]\n\t[-t/--type 车次类型1 车次类型2 ...]\n\t[-st/--starttime 出发时间下限（小时）]\n\t[-at/--arrivetime 到达时间上限（小时）]'
                exit()
    train_type_text = ''
    for item in train_type:
        train_type_text += u'%s、' % item
    print u'出发车站:', from_station[1]
    print u'到达车站:', to_station[1]
    print u'日期:', train_date
    print u'车次类型:', train_type_text[:-1]
    if start_time:
        print u'出发时间下限: %d点' % start_time
    if arrive_time:
        print u'到达时间上限: %d点59分' % arrive_time
    uri = 'https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date=%d-%02d-%02d&leftTicketDTO.from_station=%s&leftTicketDTO.to_station=%s&purpose_codes=ADULT' % (train_date.year, train_date.month, train_date.day, from_station[2], to_station[2])
    request = urllib2.Request(uri)
    request.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.93 Safari/537.36 OPR/32.0.1948.69')
    def loop():
        try:
            result = urllib2.urlopen(request, context=context, timeout = 10).read().decode('utf-8', 'ignore')
            tickets = json.loads(result)['data']
        except:
            print 'Failed'
            return
        for item in tickets:
            ticket = item['queryLeftNewDTO']
            if ticket['station_train_code'][0] in train_type and (not start_time or int(ticket['start_time'][0:2]) >= start_time) and (not arrive_time or int(ticket['arrive_time'][0:2]) <= arrive_time):
                if ticket['ze_num'] != '--':
                    num = (u'二等座', ticket['ze_num'])
                elif ticket['yz_num'] != '--':
                    num = (u'硬座', ticket['yz_num'])
                else:
                    num = None
                if num:
                    print u'[%s] %s (%s-%s|%s-%s) %s：%s' % (time.strftime('%X', time.localtime(time.time())), ticket['station_train_code'], ticket['from_station_name'], ticket['to_station_name'], ticket['start_time'], ticket['arrive_time'], num[0], num[1])
                    if num[1] not in (u'无',):
                        os.system((u'osascript -e \'display notification "[%s-%s] %s-%s" with title "有票啦！%s %s：%s" sound name "Pop.aiff"\'' % (ticket['from_station_name'], ticket['to_station_name'], ticket['start_time'], ticket['arrive_time'], ticket['station_train_code'], num[0], num[1])).encode('utf-8'))
    while True:
        loop()
        time.sleep(30)