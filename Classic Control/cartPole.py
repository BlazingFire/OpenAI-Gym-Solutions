import gym
import numpy as np
import random
import tensorflow as tf

env = gym.make('CartPole-v0')
observation = env.reset()

EPISODES = 10000
TIMESTAMP = 700
GAMMA = 0.99
ALPHA = 0.005
MOMENTUM = 0.9
explore_eps = 0.2
IN = 4
OUT = 2
BATCH_SIZE = 3

class neuralNet:
	def __init__(self,n,h1,h2,o):
		self.sess = tf.InteractiveSession()

		self.X = tf.placeholder(tf.float32,[None,n])
		self.C = tf.placeholder(tf.float32,[None,o])
		self.Y = tf.placeholder(tf.float32,[None,o])
		self.W1 = tf.Variable(tf.random_uniform(shape=[n,h1]))
		self.W2 = tf.Variable(tf.random_uniform(shape=[h1,h2]))
		self.W3 = tf.Variable(tf.random_uniform(shape=[h2,o]))
		self.B1 = tf.Variable(tf.zeros([h1]))
		self.B2 = tf.Variable(tf.zeros([h2]))
		self.B3 = tf.Variable(tf.zeros([o]))

		self.Y1 = tf.nn.sigmoid(tf.matmul(self.X,self.W1) + self.B1)
		self.Y2 = tf.nn.relu(tf.matmul(self.Y1,self.W2) + self.B2)
		self.Y3 = tf.matmul(self.Y2,self.W3) + self.B3

		self.reg_losses = tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES)
		self.reg_constant = 0.001  # Choose an appropriate one.
		self.L = tf.reduce_sum(tf.square(self.Y - tf.mul(self.Y3,self.C))) + (self.reg_constant * sum(self.reg_losses))

		self.optimizerMSGD = tf.train.MomentumOptimizer(ALPHA, MOMENTUM)
		self.optimizerRMS = tf.train.RMSPropOptimizer(learning_rate=ALPHA)
		self.train_step = self.optimizerRMS.minimize(self.L)

		self.sess.run(tf.initialize_all_variables())

	def forward_pass(self,x):
		out = self.Y3.eval(feed_dict={self.X:x.reshape(1,x.shape[0])})
		# print out
		return np.argmax(out) , np.max(out)

	def train(self,x,y,c):
		self.train_step.run(feed_dict={self.X:x , self.Y:y, self.C:c})



nnet = neuralNet(IN,10,10,OUT)
data_batch = {}

def create_new_data(ot,re,ot2,reset,done,action):
	ot = ot.reshape((1,IN))
	c = np.zeros((1,OUT))
	c[0][action] = 1
	yval = np.zeros((1,OUT))
	x , y = nnet.forward_pass(ot2)
	yval[0][action] = re
	if not done:
		yval[0][action] = re + GAMMA*y
	if reset:
		data_batch['X'] = ot
		data_batch['Y'] = yval
		data_batch['C'] = c
	else:
		data_batch['X'] = np.append(data_batch['X'],ot,axis=0)
		data_batch['Y'] = np.append(data_batch['Y'],yval,axis=0)
		data_batch['C'] = np.append(data_batch['C'],c,axis=0)


ans = np.zeros((12))
anssum = np.zeros((12))

for ep in range(EPISODES):
	observation = env.reset()
	reward = 0
	sum_reward = 0
	data_batch = {}
	reset = True
	for t in range(TIMESTAMP):
		env.render()
		x = np.array(observation)
		action, actionval = nnet.forward_pass(x)
		# print action, actionval

		tempvar = random.random()
		if tempvar < max(explore_eps,(1000.0/(ep+1))) and ep < 8000:      # dont explore for last 10000 episodes
			action = env.action_space.sample()

		# print action
		observation, reward, done, info = env.step(action)
		create_new_data(x,reward,np.array(observation),reset,done,action)
		reset = False

		if data_batch['X'].shape[0] == BATCH_SIZE:
			nnet.train(data_batch['X'] , data_batch['Y'], data_batch['C'])
			reset = True

		sum_reward = sum_reward + reward
		if done :
			nnet.train(data_batch['X'] , data_batch['Y'], data_batch['C'])
			print("Episode finished after {} timesteps.", ep ,  format(t+1))
			ans[int(ep/1000)] = max(ans[int(ep/1000)],t)
			anssum[int(ep/1000)] += anssum[int(ep/1000)]
			break

for i in range(5):
	print (i*1000 , " -- ", (i+1)*1000 , " == " , ans[i] , (anssum[i]/1000))

