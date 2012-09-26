from facerec.distance import EuclideanDistance
from facerec.util import asRowMatrix
import logging
import numpy as np
import operator as op

class AbstractClassifier(object):
	def compute(self,X,y):
		raise NotImplementedError("Every AbstractClassifier must implement the compute method.")
	
	def predict(self,X):
		raise NotImplementedError("Every AbstractClassifier must implement the predict method.")

class NearestNeighbor(AbstractClassifier):
	"""
	Implements a k-Nearest Neighbor Model for a generic distance metric.
	"""
	def __init__(self, dist_metric=EuclideanDistance(), k=1):
		AbstractClassifier.__init__(self)
		self.k = k
		self.dist_metric = dist_metric

	def compute(self, X, y):
		self.X = X
		self.y = y
	
	def predict(self, q):
		distances = []
		for xi in self.X:
			xi = xi.reshape(-1,1)
			d = self.dist_metric(xi, q)
			distances.append(d)
		if len(distances) > len(self.y):
			raise Exception("More distances than classes. Is your distance metric correct?")
		idx = np.argsort(np.array(distances))
		sorted_y = self.y[idx]
		sorted_y = sorted_y[0:self.k]
		hist = dict((key,val) for key, val in enumerate(np.bincount(sorted_y)) if val)
		return max(hist.iteritems(), key=op.itemgetter(1))[0]
		
	def __repr__(self):
		return "NearestNeighbor (k=%s, dist_metric=%s)" % (self.k, repr(self.dist_metric))

# libsvm
try:
	from svmutil import *
except ImportError:
	logger = logging.getLogger("facerec.classifier.SVM")
	logger.debug("Import Error: libsvm bindings not available.")
except:
	logger = logging.getLogger("facerec.classifier.SVM")
	logger.debug("Import Error: libsvm bindings not available.")

import sys
from StringIO import StringIO
bkp_stdout=sys.stdout

class SVM(AbstractClassifier):
	"""
	This class is just a simple wrapper to use libsvm in the 
	CrossValidation module. If you don't use this framework
	use the validation methods coming with LibSVM, they are
	much easier to access (simply pass the correct class 
	labels in svm_predict and you are done...).

	The grid search method in this class is somewhat similar
	to libsvm grid.py, as it performs a parameter search over
	a logarithmic scale.	Again if you don't use this framework, 
	use the libsvm tools as they are much easier to access.

	Please keep in mind to normalize your input data, as expected
	for the model. There's no way to assume a generic normalization
	step.
	"""

	def __init__(self, param=None):
		AbstractClassifier.__init__(self)
		self.logger = logging.getLogger("facerec.classifier.SVM")
		self.param = param
		self.svm = svm_model()
		self.param = param
		if self.param is None:
			self.param = svm_parameter("-q")
	
	def compute(self, X, y):
		self.logger.debug("SVM TRAINING (C=%.2f,gamma=%.2f,p=%.2f,nu=%.2f,coef=%.2f,degree=%.2f)" % (self.param.C, self.param.gamma, self.param.p, self.param.nu, self.param.coef0, self.param.degree))
		# turn data into a row vector (needed for libsvm)
		X = asRowMatrix(X)
		y = np.asarray(y)
		problem = svm_problem(y, X.tolist())		
		self.svm = svm_train(problem, self.param)
		self.y = y
	
	def predict(self, X):
		X = np.asarray(X).reshape(1,-1)
		sys.stdout=StringIO() 
		p_lbl, p_acc, p_val = svm_predict([0], X.tolist(), self.svm)
		sys.stdout=bkp_stdout
		return int(p_lbl[0])
	
	def __repr__(self):		
		return "Support Vector Machine (kernel_type=%s, C=%.2f,gamma=%.2f,p=%.2f,nu=%.2f,coef=%.2f,degree=%.2f)" % (KERNEL_TYPE[self.param.kernel_type], self.param.C, self.param.gamma, self.param.p, self.param.nu, self.param.coef0, self.param.degree)


