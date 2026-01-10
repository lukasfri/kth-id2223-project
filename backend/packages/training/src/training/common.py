from enum import Enum

class Operator(Enum):
    SL = "sl"
    UL = "ul"
    Sormland = "sormland"
    Otraf = "otraf"
    JLT = "jlt"
    Krono = "krono"
    KLT = "klt"
    Gotland = "gotland"
    Blekinge = "blekinge"
    Skane = "skane"
    Halland = "halland"
    VT = "vt"
    Varm = "varm"
    Orebro = "orebro"
    Vastmanland = "vastmanland"
    D_T = "dt"
    XT = "xt"
    Dintur = "dintur"
    Jamtland = "jamtland"
    Vasterbotten = "vasterbotten"
    Norrbotten = "norrbotten"
    BTbuss = "btbuss"
    DG = "dg"
    Falcks = "falcks"
    Flixbus = "flixbus"
    Harje = "harje"
    Lenna = "lenna"
    Lulea = "lulea"
    Masen = "masen"
    Malartag = "malartag"
    NorrtagVRsverige = "norrtag-vr-sverige"
    Ressel = "ressel"
    Roslagen = "roslagen"
    SJ = "sj"
    SJNorge = "sjnorge"
    Sjostadstrafiken = "sjostadstrafiken"
    Skelleftea = "skelleftea"
    Snalltaget = "snalltaget"
    Stromma = "stromma"
    TibVRsverige = "tib-vr-sverige"
    TJF = "tjf"
    Trosa = "trosa"
    Tagab = "tagab"
    Uddevalla = "uddevalla"
    VR = "vr"
    VyNorge = "vy-norge"
    VyVarmlandnorge = "vy-varmlandnorge"
    VyVarmlandstrafik = "vy-varmlandstrafik"
    Ybuss = "ybuss"

class DataType(Enum):
    STATIC = "static"
    REALTIME = "realtime"
    VEHICLE_POSITIONS = "vehicle_positions"
    OCCUPANCY = "occupancy"

class FeedID(Enum):
    ServiceAlerts = "ServiceAlerts"
    VehiclePositions = "VehiclePositions"
    TripUpdates = "TripUpdates"

DT = DataType

# Operator	Abbreviation	Static data	Real-time data	Vehicle positions	Occupancy data
# SL	sl	✔️	✔️	✔️	
# UL	ul	✔️	✔️	✔️	
# Sörmlandstrafiken	sormland	✔️			
# Östgötatrafiken	otraf	✔️	✔️	✔️	✔️
# JLT	jlt	✔️	✔️	✔️	
# Kronoberg	krono	✔️	✔️	✔️	
# KLT	klt	✔️	✔️	✔️	
# Gotland	gotland	✔️	✔️	✔️	
# Blekingetrafiken	blekinge	✔️			
# Skånetrafiken	skane	✔️	✔️	✔️	✔️
# Hallandstrafiken	halland	✔️			
# Västtrafik	vt	✔️			
# Värmlandstrafik	varm	✔️	✔️	✔️	
# Örebro	orebro	✔️	✔️	✔️	
# Västmanland	vastmanland	✔️	✔️	✔️	
# Dalatrafik	dt	✔️	✔️	✔️	
# X-trafik	xt	✔️	✔️	✔️	
# Din Tur - Västernorrland	dintur	✔️	✔️	✔️	
# Jämtland	jamtland	✔️			
# Västerbotten	vasterbotten	✔️			
# Norrbotten	norrbotten	✔️			
# BT buss	btbuss	✔️			
# Destination Gotland	dg	✔️			
# Falcks Omnibus AB	falcks	✔️			
# Flixbus	flixbus	✔️			
# Härjedalingen	harje	✔️			
# Lennakatten	lenna	✔️			
# Luleå Lokaltrafik	lulea	✔️			
# Masexpressen	masen	✔️			
# Mälartåg ersättningstrafik	malartag	✔️			
# Norrtåg ersättningsstrafik (VR Sverige)	norrtag-vr-sverige	✔️			
# Ressel Rederi	ressel	✔️			
# Roslagens sjötrafik	roslagen	✔️			
# SJ	sj	✔️			
# SJ Norge	sjnorge	✔️			
# Sjöstadstrafiken (Stockholm Stad)	sjostadstrafiken	✔️			
# Skellefteåbuss	skelleftea	✔️			
# Snälltåget	snalltaget	✔️			
# Strömma Turism & Sjöfart AB	stromma	✔️			
# TiB ersättningstrafik (VR Sverige)	tib-vr-sverige	✔️			
# TJF Smalspåret	tjf	✔️			
# Trosabussen	trosa	✔️			
# Tågab	tagab	✔️			
# Uddevalla Skärgårdsbåtar AB	uddevalla	✔️			
# VR	vr	✔️			
# Vy Norge	vy-norge	✔️			
# Vy Tåg AB	vy-varmlandnorge	✔️			
# Vy Värmlandstrafik	vy-varmlandstrafik	✔️			
# Y-Buss	ybuss	✔️
_AVAILABLE_DATA = {
    Operator.SL:                {DT.STATIC: True,  DT.REALTIME: True,  DT.VEHICLE_POSITIONS: True,  DT.OCCUPANCY: False},
    Operator.UL:                {DT.STATIC: True,  DT.REALTIME: True,  DT.VEHICLE_POSITIONS: True,  DT.OCCUPANCY: False},
    Operator.Sormland:          {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.Otraf:             {DT.STATIC: True,  DT.REALTIME: True,  DT.VEHICLE_POSITIONS: True,  DT.OCCUPANCY: True },
    Operator.JLT:               {DT.STATIC: True,  DT.REALTIME: True,  DT.VEHICLE_POSITIONS: True,  DT.OCCUPANCY: False},
    Operator.Krono:             {DT.STATIC: True,  DT.REALTIME: True,  DT.VEHICLE_POSITIONS: True,  DT.OCCUPANCY: False},
    Operator.KLT:               {DT.STATIC: True,  DT.REALTIME: True,  DT.VEHICLE_POSITIONS: True,  DT.OCCUPANCY: False},
    Operator.Gotland:           {DT.STATIC: True,  DT.REALTIME: True,  DT.VEHICLE_POSITIONS: True,  DT.OCCUPANCY: False},
    Operator.Blekinge:          {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.Skane:             {DT.STATIC: True,  DT.REALTIME: True,  DT.VEHICLE_POSITIONS: True,  DT.OCCUPANCY: True },
    Operator.Halland:           {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.VT:                {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.Varm:              {DT.STATIC: True,  DT.REALTIME: True,  DT.VEHICLE_POSITIONS: True,  DT.OCCUPANCY: False},
    Operator.Orebro:            {DT.STATIC: True,  DT.REALTIME: True,  DT.VEHICLE_POSITIONS: True,  DT.OCCUPANCY: False},
    Operator.Vastmanland:       {DT.STATIC: True,  DT.REALTIME: True,  DT.VEHICLE_POSITIONS: True,  DT.OCCUPANCY: False},
    Operator.D_T:               {DT.STATIC: True,  DT.REALTIME: True,  DT.VEHICLE_POSITIONS: True,  DT.OCCUPANCY: False},
    Operator.XT:                {DT.STATIC: True,  DT.REALTIME: True,  DT.VEHICLE_POSITIONS: True,  DT.OCCUPANCY: False},
    Operator.Dintur:            {DT.STATIC: True,  DT.REALTIME: True,  DT.VEHICLE_POSITIONS: True,  DT.OCCUPANCY: False},
    Operator.Jamtland:          {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.Vasterbotten:      {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.Norrbotten:        {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.BTbuss:            {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.DG:                {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.Falcks:            {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.Flixbus:           {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.Harje:             {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.Lenna:             {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.Lulea:             {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.Masen:             {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.Malartag:          {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.NorrtagVRsverige:  {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.Ressel:            {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.Roslagen:          {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.SJ:                {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.SJNorge:           {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.Sjostadstrafiken:  {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.Skelleftea:        {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.Snalltaget:        {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.Stromma:           {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.TibVRsverige:      {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.TJF:               {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.Trosa:             {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.Tagab:             {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.Uddevalla:         {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.VR:                {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.VyNorge:           {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.VyVarmlandnorge:   {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.VyVarmlandstrafik: {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
    Operator.Ybuss:             {DT.STATIC: True,  DT.REALTIME: False, DT.VEHICLE_POSITIONS: False, DT.OCCUPANCY: False},
}

def is_data_available(operator: Operator, data_type: DataType) -> bool:
    return _AVAILABLE_DATA.get(operator, {}).get(data_type, False)
