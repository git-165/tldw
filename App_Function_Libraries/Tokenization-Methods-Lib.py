# Tokenization-Methods-Lib.py
#########################################
# Tokenization Methods Library
# This library is used to handle tokenization of text for summarization.
#
####



####################
# Function List
#
# 1. openai_tokenize(text: str) -> List[str]
#
####################


#######################################################################################################################
# Function Definitions
#

def openai_tokenize(text: str) -> List[str]:
    encoding = tiktoken.encoding_for_model('gpt-4-turbo')
    return encoding.encode(text)

#
#
#######################################################################################################################
