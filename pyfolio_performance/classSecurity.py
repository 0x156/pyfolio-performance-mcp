from .classPortfolioPerformanceObject import PortfolioPerformanceObject

class Security(PortfolioPerformanceObject):
    """
    A class that manages securities.
    """

    referenceSkip = 0
    securityNameMap = {}
    securityIsinMap = {}
    securityWknMap = {}
    securityNums = {}
    mostRecentValue = None
    pricescale = 1000000 # scale factor to reach euro value in cents
    
    def __init__(self, data): #, name, isin, wkn):
        self._attributeList = ['uuid', 'name', 'currencyCode', 'isin', 'tickerSymbol', 'wkn', 'feed']
        self.data = data
        self.name = data["name"]
        self.logo = None
        self.isin = data["isin"] if "isin" in data else None
        self.wkn = data["wkn"] if "wkn" in data else None
        self.mostRecentValue = None
        Security.securityNums[data['num']] = self
        Security.securityNameMap[self.name] = self
        if self.isin != None:
            Security.securityIsinMap[self.isin] = self
        if self.wkn != None:
            Security.securityWknMap[self.wkn] = self

    @property
    def ticker_symbol(self):
        """Ticker symbol (e.g. 'AAPL', 'VGWL.DE', 'BTC'), if set in the XML."""
        val = self.data.get("tickerSymbol")
        return val if val else None

    @property
    def currency_code(self):
        """Currency code (e.g. 'EUR', 'USD'), if set in the XML."""
        val = self.data.get("currencyCode")
        return val if val else None

    def get_custom_attributes(self):
        """Parse <attributes><map><entry> elements into a flat key-value dict.

        Returns typed values:
        - float  for <double> entries (e.g. ter -> 0.0022)
        - int    for <long> entries   (e.g. aum -> 1000000)
        - str    for <string> entries (e.g. logo -> "data:...")
        """
        attrs = {}
        attr_elem = self.data.get("attributes")
        if not isinstance(attr_elem, dict):
            return attrs
        map_elem = attr_elem.get("map")
        if not isinstance(map_elem, dict):
            return attrs
        entries = map_elem.get("entry")
        if entries is None:
            return attrs
        if isinstance(entries, dict):
            entries = [entries]

        for entry in entries:
            if not isinstance(entry, dict):
                continue
            strings = entry.get("string")
            if strings is None:
                continue

            key = strings[0] if isinstance(strings, list) else strings
            if not key:
                continue

            value = None
            if isinstance(strings, list) and len(strings) > 1:
                value = strings[1]

            for typed_key in ("double", "long", "int"):
                if typed_key in entry:
                    raw = entry[typed_key]
                    value = float(raw) if typed_key == "double" else int(raw)
                    break

            if value is not None:
                attrs[key] = value

        return attrs

    def getLogo(self):
        """
        :return: Logo of the security
        :type: str
        """
        if self.logo != None:
            return self.logo

        try:
            attr_elem = self.data.get("attributes")
            if not isinstance(attr_elem, dict):
                return None
            map_elem = attr_elem.get("map")
            if not isinstance(map_elem, dict):
                return None
            entries = map_elem.get("entry")
            if entries is None:
                return None

            if isinstance(entries, dict):
                entries = [entries]

            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                strings = entry.get("string")
                if strings is None:
                    continue

                key = strings[0] if isinstance(strings, list) else strings
                value = None
                if isinstance(strings, list) and len(strings) > 1:
                    value = strings[1]
                for typed_key in ("double", "long", "int"):
                    if typed_key in entry:
                        value = entry[typed_key]
                        break

                if key == "logo" and value is not None:
                    self.logo = str(value)
                    break
        except (KeyError, TypeError):
            pass

        return self.logo

    @staticmethod
    def getSecurityByNum(num: int) -> 'Security':
        return Security.securityNums[num-1] # -1 because the num starts at 1

    def getMostRecentValue(self):
        """
        :return: Current security price from the file in Euro.
        :type: float
        """
        if self.mostRecentValue != None:
            return self.mostRecentValue

        prices = self.data.get("prices")
        if prices is None:
            print("No price list found for %s" % str(self))
            return 0

        priceList = prices.get("price")
        if priceList is None:
            print("No price list found for %s" % str(self))
            return 0

        if isinstance(priceList, dict):
            priceList = [priceList]

        newestDate = DateObject("0000-00-00")
        newestXml = None
        
        for price in priceList:
            if isinstance(price, str): # skip the text elements
                continue
            priceDate = DateObject(price["@t"])
            if priceDate.getOrderValue() < newestDate.getOrderValue():
                continue
            newestDate = priceDate
            newestXml = price
        
        if newestXml == None:
            self.mostRecentValue = 0
        else:    
            self.mostRecentValue = int(newestXml['@v'])/self.pricescale
        return self.mostRecentValue

    def getName(self) -> str:
        """
        :return: Name of the security
        :type: str
        """
        # return self._getXmlAttribute('name')
        return self.name

    @staticmethod
    def _getSecurityByMap(map, key):
        if key in map:
            return map[key]
        return None

    @staticmethod
    def getSecurityByName(name):
        """
        :param: Name of security that should be returned.
        :type: str

        :return: existing security object or None 
        :type: Security
        """
        return Security.securityNameMap.get(name)

    @staticmethod
    def getSecurityByIsin(isin):
        """
        :param: Isin of security that should be returned.
        :type: str

        :return: existing security object or None 
        :type: Security
        """
        return Security.securityIsinMap.get(isin)

    @staticmethod
    def getSecurityByWkn(wkn):
        """
        :param: Wkn of security that should be returned.
        :type: str

        :return: existing security object or None 
        :type: Security
        """
        return Security.securityWknMap.get(wkn)

    @staticmethod
    def parseContent(data):
        return Security(data)

    def __repr__(self) -> str:
        return "Security/%s" % self.getName()

from .classDateObject import *