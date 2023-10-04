# Providing the entire updated function for the user

def riskCodeAndPerc_left_first(text, riskPer, riskCodeList, used_codes):
    output = []
    text = re.sub('[^A-Za-z0-9%.]+', ' ', text)
    text = text.replace("at", "")
    textSplit = text.split()
    
    # Find the index of riskPer in textSplit
    value = None
    if riskPer in textSplit:
        value = textSplit.index(str(riskPer))
    else:
        for i in textSplit:
            if riskPer in i:
                value = textSplit.index(str(i))
                break

    if value is None:
        return None

    # Check for risk codes immediately to the left and right of the identified percentage
    leftInd = value - 1
    rightInd = value + 1

    # Giving preference to the left side
    if leftInd >= 0 and textSplit[leftInd] in riskCodeList and textSplit[leftInd] not in used_codes:
        used_codes.append(textSplit[leftInd])
        return [textSplit[leftInd], riskPer]
    elif rightInd < len(textSplit) and textSplit[rightInd] in riskCodeList and textSplit[rightInd] not in used_codes:
        used_codes.append(textSplit[rightInd])
        return [textSplit[rightInd], riskPer]

    return None

def riskCodeAndPercentageExtractor_continuous_corrected(text, riskCodeList, tok):
    if text:
        token = tok.lower()
        x = re.findall(r'[\d\. \d\%]*%+', text)
        riskCodeData = []
        used_codes = []  # To keep track of risk codes that have been associated
        if x:
            riskCode = []
            riskPercentage = []
            ind = text.lower().find(token)
            newText = text[ind+len(token)+1:]
            for i in x:
                value = riskCodeAndPerc_left_first(newText, i.strip(), riskCodeList, used_codes)
                if value:
                    riskCode.append(value[0])
                    riskPercentage.append(value[1])
                    # Remove the identified risk code and percentage from the newText
                    pattern = re.escape(value[0]) + r'.*?' + re.escape(value[1])
                    newText = re.sub(pattern, '', newText, count=1).strip()
            return [riskCode, riskPercentage]
        else:
            text = re.sub('[^A-Za-z0-9%.]+', " ", text)
            ind = text.lower().find(token)
            newText = text[ind+len(token):]
            newText = newText.split()
            for i in newText:
                if i in riskCodeList:
                    riskCodeData.append(i)
            return [riskCodeData, None]

riskCodeAndPercentageExtractor_continuous_corrected


import re

def riskCodeAndPerc_strict_order_revised(text, riskCodeList, used_codes):
    output = []
    text = re.sub('[^A-Za-z0-9%.]+', ' ', text)
    text = text.replace("at", "")
    textSplit = text.split()
    
    idx = 0
    while idx < len(textSplit):
        part = textSplit[idx]
        
        if "%" in part:
            # Check left
            if idx > 0 and textSplit[idx-1] in riskCodeList and textSplit[idx-1] not in used_codes:
                used_codes.append(textSplit[idx-1])
                output.append([textSplit[idx-1], part])
                idx += 1  # Move to next part after percentage
                continue
            # Check right
            elif idx < len(textSplit) - 1 and textSplit[idx+1] in riskCodeList and textSplit[idx+1] not in used_codes:
                used_codes.append(textSplit[idx+1])
                output.append([textSplit[idx+1], part])
                idx += 2  # Move to next part after risk code
                continue
        
        idx += 1

    # Ensure that each percentage is associated with only one risk code
    used_percentages = []
    unique_output = []
    for pair in output:
        if pair[1] not in used_percentages:
            unique_output.append(pair)
            used_percentages.append(pair[1])
    
    return unique_output

def riskCodeAndPercentageExtractor_strict_order_final(text, riskCodeList, tok):
    if text:
        token = tok.lower()
        riskCodeData = []
        used_codes = []  # To keep track of risk codes that have been associated
        
        ind = text.lower().find(token)
        newText = text[ind+len(token)+1:]
        
        # Adjusting the regex pattern again to correctly capture percentages
        percentages = re.findall(r'(\d{1,3}\s*%)', newText)
        
        pairs = riskCodeAndPerc_strict_order_revised(newText, riskCodeList, used_codes)
        
        riskCode = [pair[0] for pair in pairs]
        riskPercentage = [pair[1] for pair in pairs]
        
        return [riskCode, riskPercentage]
    else:
        text = re.sub('[^A-Za-z0-9%.]+', " ", text)
        ind = text.lower().find(token)
        newText = text[ind+len(token):]
        newText = newText.split()
        for i in newText:
            if i in riskCodeList:
                riskCodeData.append(i)
        return [riskCodeData, None]

