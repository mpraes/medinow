import pywhatkit as pwk
 
# using Exception Handling to avoid unexpected errors
try:
     # sending message in Whatsapp in India so using Indian dial code (+91)
     pwk.sendwhatmsg("+5515991367797", "Hi, how are you?", 20, 34)
 
     print("Message Sent!") #Prints success message in console
 
     # error message
except Exception as e: 
     print(f"Error in sending the message: {e}")