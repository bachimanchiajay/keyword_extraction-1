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
