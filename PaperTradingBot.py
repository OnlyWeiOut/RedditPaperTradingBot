import praw
import config
import time
from bs4 import BeautifulSoup
import urllib
import datetime

class Account(object):
	accountBalance = 10000.00
	stocksInPortfolio = {}


class Stock(object):
	amountOfShares = 0
	averagePrice = 0.0
	ticker = ""

def get_current_price(ticker):

	url = "http://www.nasdaq.com/symbol/"+ticker
	r = urllib.urlopen(url).read()
	soup = BeautifulSoup(r, "lxml")
	priceWithTag = soup.find("div", class_="qwidget-dollar")

	if priceWithTag is None: 
		return None
	price = priceWithTag.find(text=True)
	price = float(price.replace("$", ""))

	return price

def bot_login():
	r = praw.Reddit(username = config.username,
			password = config.password,
			client_id = config.client_id,
			client_secret = config.client_secret,
			user_agent = "onlyweiout's whatever test")
	return r

def open_new_account(comment):
	author = comment.author
	name = author.name

	if name in dictionaryOfAccounts:
		print "You already have an account!"
	else:
		newAccountForUser = Account()
		dictionaryOfAccounts[name] = newAccountForUser
		print "New Account Opened for User: " + author.name

def buy_shares(comment):
	author = comment.author
	name = author.name

	if name not in dictionaryOfAccounts:
		print "You do not have an account with me. Please open an account."
	else:
		accountOfUser = dictionaryOfAccounts[name]
		redditComment = str(comment.body) #Chance from Unicode to String
		wordsInComment = redditComment.split(" ")

		index = 0
		for word in wordsInComment:
			balanceOfUser = accountOfUser.accountBalance
			stocksInPortfolio = accountOfUser.stocksInPortfolio
			index += 1
			if len(wordsInComment) < index + 1:
				break

			if word == 'buy':
				try:
					buyThisManyNumberOfShares = int(wordsInComment[index])
				except ValueError:
					print "You did not buy anything because the error was wrong."
					break
				ticker = wordsInComment[index + 1].replace("$", "").replace(" ", "")
			
				price = get_current_price(ticker)
				if price is None:
					break
				transactionCost = price * buyThisManyNumberOfShares

				if transactionCost > balanceOfUser:
					print "You cannot afford this many shares. Please try again."
				else:
					print "You just bought " + str(buyThisManyNumberOfShares) + " of $" + ticker +"!!"

					if ticker in stocksInPortfolio:
						#Change balance 
						dictionaryOfAccounts[name].accountBalance -= transactionCost

						currentAmountOfShares = dictionaryOfAccounts[name].stocksInPortfolio[ticker].amountOfShares
						currentAveragePrice = dictionaryOfAccounts[name].stocksInPortfolio[ticker].averagePrice
						
						dictionaryOfAccounts[name].stocksInPortfolio[ticker].amountOfShares += buyThisManyNumberOfShares
						dictionaryOfAccounts[name].stocksInPortfolio[ticker].averagePrice = ((currentAveragePrice*currentAmountOfShares) + transactionCost)/(dictionaryOfAccounts[name].stocksInPortfolio[ticker].amountOfShares)

					else:

						dictionaryOfAccounts[name].accountBalance -= transactionCost
						newStock = Stock()
						newStock.amountOfShares = buyThisManyNumberOfShares 
						newStock.ticker = ticker
						newStock.averagePrice = price

						dictionaryOfAccounts[name].stocksInPortfolio[ticker] = newStock


def sell_shares(comment):
	
	author = comment.author
	name = author.name

	if name not in dictionaryOfAccounts:
		print "You do not have an account with me. Please open an account."
	else:
		redditComment = str(comment.body) #Chance from Unicode to String
		wordsInComment = redditComment.split(" ")

		index = 0
		for word in wordsInComment:
			balanceOfUser = dictionaryOfAccounts[name].accountBalance
			stocksInPortfolio = dictionaryOfAccounts[name].stocksInPortfolio
			index += 1
			if len(wordsInComment) < index + 1:
				break

			if word == 'sell':
				try:
					sellThisManyNumberOfShares = int(wordsInComment[index])
				except ValueError:
					print "You did not sell anything because the input was wrong."
					break
				ticker = wordsInComment[index + 1].replace("$", "").replace(" ", "")
				

				if ticker not in dictionaryOfAccounts[name].stocksInPortfolio:
					print "You do not own this stock."
				else:
					currentAmountOfShares = dictionaryOfAccounts[name].stocksInPortfolio[ticker].amountOfShares
					if currentAmountOfShares < sellThisManyNumberOfShares:
						sellThisManyNumberOfShares = currentAmountOfShares


					price = get_current_price(ticker)
					if price is None:
						break
					totalSales = price * sellThisManyNumberOfShares


					dictionaryOfAccounts[name].accountBalance += totalSales
					dictionaryOfAccounts[name].stocksInPortfolio[ticker].amountOfShares -= sellThisManyNumberOfShares

					if dictionaryOfAccounts[name].stocksInPortfolio[ticker].amountOfShares is 0:
						dictionaryOfAccounts[name].stocksInPortfolio.pop(ticker, None)
					print "You just sold " + str(sellThisManyNumberOfShares) + " of $" + ticker +"!!"

def current_portfolio(comment):
	author = comment.author
	name = author.name

	if name not in dictionaryOfAccounts:
		print "You do not have an account with me. Please open an account."
	else:

		table = "Ticker|# Shares|Avg|Current|Change\n:--|:--|:--|:--|:--\n"
		print "Portfolio Owner: " + name
		print "Portfolio Cash: " + str(dictionaryOfAccounts[name].accountBalance)
		valueInStocks = 0.0
		for stock in dictionaryOfAccounts[name].stocksInPortfolio:
			amountOfShares = dictionaryOfAccounts[name].stocksInPortfolio[stock].amountOfShares
			ticker = dictionaryOfAccounts[name].stocksInPortfolio[stock].ticker
			averagePrice = dictionaryOfAccounts[name].stocksInPortfolio[stock].averagePrice
			currentPrice = get_current_price(ticker)
			valueInStocks+=(currentPrice * amountOfShares)
			percentChange = str(((currentPrice/averagePrice) - 1.0) * 100) + "%"
			table += ""+ticker+"|"+str(amountOfShares)+"|"+str(averagePrice)+"|"+str(currentPrice)+"|"+percentChange+"\n "
			#print "$"+ticker + ": " + str(amountOfShares) + " shares at an average price of " + str(averagePrice) + "."
		print table
		totalValueOfAccount = valueInStocks + dictionaryOfAccounts[name].accountBalance
		totalPercentChange = str(((totalValueOfAccount/10000) - 1) * 100) + "%"
		response = "Portfolio Owner: "+name + "\n\n"+"Account Total Value: " + str(totalValueOfAccount)+"|"+totalPercentChange+"\n\n"+"Portfolio Available Cash: "+str(dictionaryOfAccounts[name].accountBalance)+"\n\n"
		response += table
		comment.reply(response)
def help_please(comment):
	comment.reply("Command|Example|Action\n :--|:--|:--\n Open Account|'PaperTradingBot, open account'|Open a new Account.\n Buy|'PaperTradingBot buy 10 $AAPL'|Buy # shares of stock.\n Sell| 'PaperTradingBot sell 10 $AAPL'| Sells # shares of stock\n")

def run_bot(r):
	for comment in r.subreddit('test').comments(limit = 5):
		if 'PaperTradingBot' in comment.body and comment.id not in comments_replied_to:
			if 'open account' in comment.body:
				open_new_account(comment)
			elif 'check portfolio' in comment.body:
				current_portfolio(comment)
			elif 'buy' in comment.body:
				buy_shares(comment)
			elif 'sell' in comment.body:
				sell_shares(comment)
			elif 'help' in comment.body:
				help_please(comment)
			else:
				print comment.body

			comments_replied_to.append(comment.id)

r = bot_login()
comments_replied_to = []
dictionaryOfAccounts = {}

dateTime = datetime.datetime.now()
time = dateTime.time()



while True:
	run_bot(r)

