import logging
from utils.color import color

logging.basicConfig(level = logging.INFO)

LOGGER=logging.getLogger(__name__)

# Define a custom logging handler that calls a callback after emitting a log record
class CallbackStreamHandler(logging.StreamHandler):
    def __init__(self, stream=None):
        super().__init__(stream)

    def emit(self, record):
        if record.args and 'TRANSACTION' not in record.msg :
            record.msg=f"{record.msg} {record.args['stock']} at {record.args['date']}"
            if 'SELL' in record.msg :
                record.msg=record.msg+f" bought at {color.BLUE}{record.args['date_of_buy']}{color.RESET}"
        super().emit(record)  # Emit the log record (this will print the log message)
        if record.args and 'TRANSACTION'  not in record.msg :
             table_content=[record.args['funds_before_transaction'],record.args['money_involved'],record.args['funds_after_transaction'],record.args['volume'],record.args['price_at_transaction_time']]
             self.make_table(table_content)
                

         

    def make_table(self,val):
        table=[]
        headers=['Previous Funds ($)','Order ($)','New Funds ($)','Volume','Unit price ($)']
        table.append(headers)
        table.append(val)
        self.print_table(table)

    def print_table(self,table_content):
        headers,row1=table_content[0],table_content[1]


        # Determine the width of each column
        col_widths = [max(len(str(item)) for item in column) for column in zip(headers, row1)]

        # Print the headers
        header_row = " | ".join(f"{header:<{width}}" for header, width in zip(headers, col_widths))
        separator_row = "---".join("-" * width for width in col_widths)
        print(header_row)
        print(separator_row)

        # Print the rows
        data_rows = [row1]
        for row in data_rows:
            formatted_row = " | ".join(f"{item:<{width}}" for item, width in zip(row, col_widths))
            print(formatted_row)
        print('')
    


class ColoredFormatter(logging.Formatter):

    INFO=color.BLUE+color.BOLD
    WARNING=color.YELLOW+color.BOLD
    ERROR=color.RED+color.BOLD
    BUY_COLOR=color.BLUE
    SELL_COLOR=color.GREEN
    TRANSACTION_COLOR=color.YELLOW


        
    def format(self, record):
   
        log_color =  getattr(self,record.levelname) 
        record.levelname = f"{log_color}[{record.levelname}]{color.RESET}"
        record.msg=self.check_msg(record.msg,record.args)

        formatted_message = f"{record.levelname} - {record.msg}"
       
        return formatted_message

    def check_msg(self,string,arg):
        if 'BUY' in string:
           string=self.BUY_COLOR+string+color.RESET
        if 'SELL' in string:
           string=self.SELL_COLOR+string+color.RESET
        if 'TRANSACTION' in string:
            string=string.replace('TRANSACTION',self.TRANSACTION_COLOR+'TRANSACTION'+color.RESET)
            string =string +': '
            arg=arg[0]
            if arg > 0:
                val=color.GREEN+ str(arg)+color.RESET
            elif arg < 0:
                val=color.RED+ str(arg)+color.RESET
            else:
                val=str(arg)
            string =string +': '+val +' $ \n'
        return string



handler = CallbackStreamHandler()


formatter = ColoredFormatter()

handler.setFormatter(formatter)

# Add the handler to the logger
LOGGER.addHandler(handler)
LOGGER.propagate = False