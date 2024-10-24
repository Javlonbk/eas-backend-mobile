from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select, Session
from typing import Annotated
from dbapi import Relay, Report, Item, Token, get_session, create_db_and_tables
import uvicorn
from threading import Thread
from time import sleep
from pyModbusTCP.client import ModbusClient
from datetime import datetime, timedelta
from detectorControl import start_def, stop_def
import openpyxl

client = ModbusClient(host='192.168.21.77', port=9999, unit_id=1, auto_close=True)

threading_break = False
check_status = False
token = ""
sensorname = ""

def waitingDeadline(sleepTime):
    global threading_break, check_status
    sleep_ms = 0.0
    print('>>> DEBUG >>>', sleepTime)
    while threading_break == False:
        if sleep_ms < sleepTime:
            sleep_ms += 0.1
        else:
            break
        sleep(0.1)
    client.write_multiple_coils(16, [0,0,0,0,0,0,0,0])
    print('>>> DEBUG >>> Thread break')
    threading_break = False
    check_status = False

SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event('startup')
def on_startup():
    if client.open() == True:
        print(f"Modbus client is connected to host: {client.host}:{client.port}...")
    else:
        print(f"Modbus connection fail!")
    create_db_and_tables()

@app.get('/reports-csv', response_class=FileResponse)
async def getReportsCSV(session: SessionDep):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(['Chastotalar', 'Boshlash vaqti', 'Tugash vaqti'])
    reports = session.exec(select(Report)).all()
    for report in reports:
        sheet.append([report.frequencies, report.startTime, report.endTime])
    file_path = 'reports.xlsx'
    workbook.save(file_path)
    return FileResponse(file_path)

@app.post('/relay-add')
def createRelay(relay: Relay, session: SessionDep) -> Relay:
    session.add(relay)
    session.commit()
    session.refresh(relay)
    return relay

@app.get('/data')
def getRelayList(session: SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100) -> list[Relay]:
    relays = session.exec(select(Relay).offset(offset).limit(limit)).all()
    return relays

@app.delete('/relay-remove/{relay_id}')
def deleteRelay(relay_id: int, session: SessionDep):
    relay = session.get(Relay, relay_id)
    if not relay:
        raise HTTPException(status_code=404, detail='Relay not found!')
    session.delete(relay)
    session.commit()
    return {"OK": True}

@app.get('/reports')
def getRelayList(session: SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100) -> list[Report]:
    reports = session.exec(select(Report).offset(offset).limit(limit).order_by(Report.id.desc())).all()
    return reports

@app.post("/insert")
async def insertData(item: Item, session: SessionDep):
    global check_status, token, dedline, threading_break, sensorname
    ports = item.ports
    dedline = item.dedline
    token = item.token
    relays = session.exec(select(Relay)).all()
    rep = [port.get('relay_port') for port in ports]
    relay_hzs = filter(None, [relay.relay_hz if relay.relay_port in rep else None for relay in relays])
    relay_state = [1 if relay.relay_port in rep else 0 for relay in relays]
    endtime = datetime.now()
    endtime = endtime + timedelta(0, int(dedline))
    session.add(Report(frequencies=', '.join(relay_hzs), deadline=dedline, endTime=endtime))
    session.commit()
    client.write_multiple_coils(16, relay_state)
    check_status = True
    threading_break = False
    Thread(target=waitingDeadline, kwargs={'sleepTime': dedline}).start()
    start_def(token=token, duration=dedline, sensor=sensorname)
    return {"OK": True}

@app.post("/delete")
async def deletData(item: Token, session: SessionDep):
    token = item.token
    global check_status, threading_break, sensorname
    lastItem: Report = session.query(Report).order_by(Report.id.desc()).first()
    lastItem.endTime = datetime.now()
    session.query(Report).filter(Report.id == lastItem.id).update({Report.endTime: lastItem.endTime})
    session.commit()
    if threading_break == False:
        threading_break = True
    if check_status == True:
        check_status = False
    
    stop_def(token=token, sensor=sensorname)
    return {"OK": True}
    
@app.get("/check")
async def checkStatus(request: Request):
    global check_status, sensorname
    sensorname = request.headers.get('sensor')
    data = client.read_input_registers(0,2)
    if data == None:
        return {"status": "error"}
    voltage = data[0] + 1
    temperature = data[1] + 1
    temperature = temperature * 5.0 / 1024.0
    voltage = voltage * 5.00 / 1024.0
    return {"data": check_status, "voltage": voltage, "temperature": temperature}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")