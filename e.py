def riskCodeAndPerc(text, percentage, riskCodeList):
    # Check to the left of the percentage for a risk code
    for riskCode in riskCodeList:
        pattern_left = riskCode + r"\s*" + percentage
        pattern_right = percentage + r"\s*" + riskCode
        if re.search(pattern_left, text):
            return (riskCode, percentage)
        elif re.search(pattern_right, text):
            return (riskCode, percentage)
    return None

def riskCodeAndPercentageExtractor(text, riskCodeList, tok):
    if not text:
        return [None, None]

    token = tok.lower()
    x = re.findall(r'[\d\. \d\%]*%+', text)
    riskCodeData = []
    riskcode = []
    riskPercentage = []

    if x:
        ind = text.lower().find(token)
        newText = text[ind+len(token)+1:]

        for percentage in x:
            value = riskCodeAndPerc(newText, percentage, riskCodeList)
            if value:
                riskcode.append(value[0])
                riskPercentage.append(value[1])
                # Remove the identified risk code and percentage from newText
                pattern = re.escape(value[0]) + r"\s*" + re.escape(value[1])  # Escaping in case of special characters
                newText = re.sub(pattern, "", newText).strip()

        return [riskcode, riskPercentage]

    else:
        text = re.sub('[^A-Za-z0-9%.]+', " ", text)
        ind = text.lower().find(token)
        newText = text[ind+len(token):]
        newText = newText.split()
        for i in newText:
            if i in riskCodeList:
                riskCodeData.append(1)
        return [riskCodeData, None]

# Testing the function with the provided text again
riskCodeAndPercentageExtractor("ALLOCATION OF PREMIUM TO CODING: 7T 1% CY 98% AG 1% NB 1% REGULATORY CLIENT", ["7T", "CY", "AG", "NB"], "CODING:")
