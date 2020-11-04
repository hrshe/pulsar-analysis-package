import configparser

config = configparser.ConfigParser()

config.read('config.txt')
#config.get('pulsar-config')
config.set('pulsar-config', 'new', '3')
config.set('pulsar-config', 'test', '5')

with open('config.txt', 'w') as configfile:
    config.write(configfile)