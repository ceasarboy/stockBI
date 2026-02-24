from typing import List, Optional, Dict
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import logging
logger = logging.getLogger(__name__)


class AkShareProvider:
    def __init__(self):
        self.name = "akshare"
    
    def get_stock_list(self) -> pd.DataFrame:
        import akshare as ak
        try:
            df = ak.stock_zh_a_spot_em()
            df = df[['代码', '名称', '最新价', '涨跌幅', '成交量', '成交额', '市盈率-动态', '市净率']]
            df.columns = ['symbol', 'name', 'close', 'change_pct', 'volume', 'amount', 'pe', 'pb']
            return df
        except Exception as e:
            logger.error(f"AkShare get_stock_list error: {e}")
            return pd.DataFrame()
    
    def get_stock_daily(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        import akshare as ak
        try:
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
            
            # 检查是否返回空数据
            if df is None or df.empty:
                logger.warning(f"AKShare returned empty data for {symbol}")
                return pd.DataFrame()
            
            # 检查返回的列名
            logger.info(f"AKShare returned columns for {symbol}: {list(df.columns)}")
            
            # 列名映射（处理不同版本的AKShare）
            column_mapping = {
                '日期': 'trade_date',
                '开盘': 'open',
                '最高': 'high',
                '最低': 'low',
                '收盘': 'close',
                '成交量': 'volume',
                '成交额': 'amount',
                '换手率': 'turnover_rate'
            }
            
            # 检查必要的列是否存在
            missing_columns = [col for col in column_mapping.keys() if col not in df.columns]
            if missing_columns:
                logger.error(f"AKShare missing columns for {symbol}: {missing_columns}")
                return pd.DataFrame()
            
            # 重命名列
            df = df[list(column_mapping.keys())].copy()
            df.columns = list(column_mapping.values())
            
            # 将日期字符串转换为date对象（不是datetime），以便与数据库兼容
            df['trade_date'] = pd.to_datetime(df['trade_date']).dt.date
            return df
        except Exception as e:
            logger.error(f"AkShare get_stock_daily error for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_stock_info(self, symbol: str) -> Dict:
        import akshare as ak
        try:
            df = ak.stock_individual_info_em(symbol=symbol)
            info = dict(zip(df['item'], df['value']))
            return info
        except Exception as e:
            logger.error(f"AkShare get_stock_info error for {symbol}: {e}")
            return {}
    
    def get_realtime_quote(self, symbol: str = None) -> pd.DataFrame:
        """获取实时行情数据"""
        import akshare as ak
        try:
            df = ak.stock_zh_a_spot_em()
            # 重命名列
            column_mapping = {
                '序号': 'seq',
                '代码': 'symbol',
                '名称': 'name',
                '最新价': 'price',
                '涨跌幅': 'change_pct',
                '涨跌额': 'change',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '最高': 'high',
                '最低': 'low',
                '今开': 'open',
                '昨收': 'pre_close',
                '量比': 'volume_ratio',
                '换手率': 'turnover_rate',
                '市盈率-动态': 'pe',
                '市净率': 'pb',
                '总市值': 'market_cap',
                '流通市值': 'float_market_cap',
                '涨速': 'change_speed',
                '5分钟涨跌': 'change_5min',
                '60日涨跌幅': 'change_60d',
                '年初至今涨跌幅': 'change_ytd'
            }
            df = df.rename(columns=column_mapping)
            
            # 如果指定了股票代码，筛选该股票
            if symbol:
                df = df[df['symbol'] == symbol]
            
            return df
        except Exception as e:
            logger.error(f"AkShare get_realtime_quote error: {e}")
            return pd.DataFrame()
    
    def get_intraday_data(self, symbol: str) -> pd.DataFrame:
        """获取分时数据"""
        import akshare as ak
        try:
            df = ak.stock_intraday_em(symbol=symbol)
            # 重命名列
            column_mapping = {
                '时间': 'time',
                '成交价': 'price',
                '手数': 'volume',
                '买卖盘性质': 'direction'
            }
            df = df.rename(columns=column_mapping)
            return df
        except Exception as e:
            logger.error(f"AkShare get_intraday_data error for {symbol}: {e}")
            return pd.DataFrame()


class BaostockProvider:
    def __init__(self):
        self.name = "baostock"
        self._bs = None
    
    def _login(self):
        import baostock as bs
        try:
            lg = bs.login()
            if lg is None:
                logger.error("Baostock login returned None")
                return False
            if hasattr(lg, 'error_code') and lg.error_code != '0':
                logger.error(f"Baostock login error: {lg.error_msg}")
                return False
            return True
        except Exception as e:
            logger.error(f"Baostock login exception: {e}")
            return False
    
    def _logout(self):
        import baostock as bs
        bs.logout()
    
    def get_stock_list(self) -> pd.DataFrame:
        import baostock as bs
        try:
            self._login()
            rs = bs.query_stock_basic()
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            df = pd.DataFrame(data_list, columns=rs.fields)
            df = df[df['type'] == '1']
            df = df[['code', 'code_name']]
            df.columns = ['symbol', 'name']
            df['symbol'] = df['symbol'].str.replace('sh.', '').str.replace('sz.', '')
            
            # 根据股票代码判断交易所
            def get_exchange(symbol):
                if symbol.startswith('688'):
                    return 'SH'  # 科创板
                elif symbol.startswith('300') or symbol.startswith('301'):
                    return 'SZ'  # 创业板（300和301开头）
                elif symbol.startswith('920') or symbol.startswith('8'):
                    return 'BJ'  # 北交所
                elif symbol.startswith('6'):
                    return 'SH'  # 上证主板
                elif symbol.startswith('0') or symbol.startswith('3'):
                    return 'SZ'  # 深证主板
                else:
                    return 'OTHER'
            
            df['exchange'] = df['symbol'].apply(get_exchange)
            
            self._logout()
            return df
        except Exception as e:
            logger.error(f"Baostock get_stock_list error: {e}")
            return pd.DataFrame()
    
    def get_stock_daily(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        import baostock as bs
        try:
            if not self._login():
                logger.error(f"Baostock login failed for {symbol}")
                return pd.DataFrame()
            
            # baostock需要 YYYY-MM-DD 格式
            # 如果传入的是 YYYYMMDD 格式，需要转换
            if len(start_date) == 8 and '-' not in start_date:
                start_date = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
            if len(end_date) == 8 and '-' not in end_date:
                end_date = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
            
            code = f"sh.{symbol}" if symbol.startswith('6') else f"sz.{symbol}"
            rs = bs.query_history_k_data_plus(
                code,
                "date,code,open,high,low,close,volume,amount,turn",
                start_date=start_date, end_date=end_date,
                frequency="d", adjustflag="2"
            )
            
            if rs is None:
                logger.error(f"Baostock query returned None for {symbol}")
                self._logout()
                return pd.DataFrame()
            
            if not hasattr(rs, 'error_code'):
                logger.error(f"Baostock query response invalid for {symbol}")
                self._logout()
                return pd.DataFrame()
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            if not data_list:
                logger.warning(f"Baostock returned no data for {symbol}")
                self._logout()
                return pd.DataFrame()
            
            df = pd.DataFrame(data_list, columns=rs.fields)
            df.columns = ['trade_date', 'symbol', 'open', 'high', 'low', 'close', 'volume', 'amount', 'turnover_rate']
            # 将日期字符串转换为date对象（不是datetime），以便与数据库兼容
            df['trade_date'] = pd.to_datetime(df['trade_date']).dt.date
            for col in ['open', 'high', 'low', 'close', 'volume', 'amount', 'turnover_rate']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            self._logout()
            return df
        except Exception as e:
            logger.error(f"Baostock get_stock_daily error for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_stock_minute(self, symbol: str, start_date: str, end_date: str, frequency: str = "5") -> pd.DataFrame:
        """获取分钟线数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            frequency: 分钟频率，可选 5, 15, 30, 60
        """
        import baostock as bs
        try:
            if not self._login():
                logger.error(f"Baostock login failed for {symbol}")
                return pd.DataFrame()
            
            # baostock需要 YYYY-MM-DD 格式
            if len(start_date) == 8 and '-' not in start_date:
                start_date = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
            if len(end_date) == 8 and '-' not in end_date:
                end_date = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
            
            code = f"sh.{symbol}" if symbol.startswith('6') else f"sz.{symbol}"
            rs = bs.query_history_k_data_plus(
                code,
                "date,time,code,open,high,low,close,volume,amount,adjustflag",
                start_date=start_date, end_date=end_date,
                frequency=frequency, adjustflag="3"
            )
            
            if rs is None or not hasattr(rs, 'error_code'):
                logger.error(f"Baostock minute query failed for {symbol}")
                self._logout()
                return pd.DataFrame()
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            if not data_list:
                logger.warning(f"Baostock returned no minute data for {symbol}")
                self._logout()
                return pd.DataFrame()
            
            df = pd.DataFrame(data_list, columns=rs.fields)
            df.columns = ['date', 'time', 'symbol', 'open', 'high', 'low', 'close', 'volume', 'amount', 'adjustflag']
            
            # 转换数据类型
            for col in ['open', 'high', 'low', 'close', 'volume', 'amount']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 解析时间字段 (格式: YYYYMMDDHHMMSSSSS)
            df['datetime'] = pd.to_datetime(df['time'], format='%Y%m%d%H%M%S%f', errors='coerce')
            
            self._logout()
            return df
        except Exception as e:
            logger.error(f"Baostock get_stock_minute error for {symbol}: {e}")
            return pd.DataFrame()


class DataProviderManager:
    def __init__(self):
        self.akshare = AkShareProvider()
        self.baostock = BaostockProvider()
        self.primary = "baostock"
        self.fallback = "akshare"
        self.available_providers = ["akshare", "baostock"]

    def test_connection(self) -> Dict:
        results = {"akshare": False, "baostock": False}
        try:
            import akshare as ak
            ak.stock_zh_a_spot_em()
            results["akshare"] = True
        except:
            pass
        try:
            import baostock as bs
            lg = bs.login()
            if lg.error_code == '0':
                results["baostock"] = True
            bs.logout()
        except:
            pass
        return results

    def get_stock_list(self) -> pd.DataFrame:
        if self.primary == "akshare":
            df = self.akshare.get_stock_list()
            if df.empty:
                logger.warning("AkShare failed, falling back to Baostock")
                df = self.baostock.get_stock_list()
        else:
            df = self.baostock.get_stock_list()
            if df.empty:
                logger.warning("Baostock failed, falling back to AkShare")
                df = self.akshare.get_stock_list()
        return df

    def get_stock_daily(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        # 统一日期格式处理
        # akshare需要 YYYYMMDD 格式
        # baostock需要 YYYY-MM-DD 格式
        
        # 转换日期格式
        akshare_start = start_date.replace("-", "") if "-" in start_date else start_date
        akshare_end = end_date.replace("-", "") if "-" in end_date else end_date
        baostock_start = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}" if len(start_date) == 8 and "-" not in start_date else start_date
        baostock_end = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}" if len(end_date) == 8 and "-" not in end_date else end_date
        
        if self.primary == "akshare":
            df = self.akshare.get_stock_daily(symbol, akshare_start, akshare_end)
            if df.empty:
                logger.warning(f"AkShare failed for {symbol}, falling back to Baostock")
                df = self.baostock.get_stock_daily(symbol, baostock_start, baostock_end)
        else:
            df = self.baostock.get_stock_daily(symbol, baostock_start, baostock_end)
            if df.empty:
                logger.warning(f"Baostock failed for {symbol}, falling back to AkShare")
                df = self.akshare.get_stock_daily(symbol, akshare_start, akshare_end)
        return df

    def switch_provider(self, provider: str):
        if provider == "akshare":
            self.primary = "akshare"
            self.fallback = "baostock"
        else:
            self.primary = "baostock"
            self.fallback = "akshare"
    
    def get_realtime_quote(self, symbol: str = None) -> pd.DataFrame:
        """获取实时行情数据（使用akshare）"""
        return self.akshare.get_realtime_quote(symbol)
    
    def get_intraday_data(self, symbol: str) -> pd.DataFrame:
        """获取分时数据（使用akshare）"""
        return self.akshare.get_intraday_data(symbol)
    
    def get_stock_minute(self, symbol: str, start_date: str = None, end_date: str = None, frequency: str = "5") -> pd.DataFrame:
        """获取分钟线数据（使用baostock）
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)，默认最近5个交易日
            end_date: 结束日期 (YYYY-MM-DD)，默认今天
            frequency: 分钟频率，可选 5, 15, 30, 60
        """
        from datetime import datetime, timedelta
        
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        return self.baostock.get_stock_minute(symbol, start_date, end_date, frequency)
