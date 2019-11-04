import copy
import MathAndStats as ms
import GaussianNeuron as gaussian
import Neuron as unit

class RBFNetwork:

    def __init__(self, means, clusts, clsses, uses_regression, logistic_output):
        self.hidden_layer = []
        self.output_layer = []
        self.uses_regression = uses_regression
        # in the case of regression, overwrite these inputs
        if uses_regression:
            out_k = 1
            logistic_output = False
        else:
            out_k = len(clsses)

        self.out_k = out_k
        # add hidden Gaussians
        for hidden_node in range(len(means)):
            self.hidden_layer.append(gaussian.GaussianNeuron(means[hidden_node], clusts[hidden_node]))
        # add output node(s)
        for output_node in range(out_k):
            self.output_layer.append(unit.Neuron(len(means), logistic_output))
            if not uses_regression:
                self.output_layer[output_node].setClass(clsses[output_node])
        #trainOutputLayer

    def getHiddenOutput(self, new_obs):
        data = [0] * (len(self.hidden_layer)+1)
        # bias node
        data[0] = 1
        for hidden_node_num in range(len(self.hidden_layer)):
            data[hidden_node_num+1] = self.hidden_layer[hidden_node_num].getOutput(new_obs)
        return data

    # Gradient Descent
    def trainOutputLayer(self, input_data, eta, alpha):
        #data = self.getHiddenOutput(input_data)
        data = []
        for example_num in range(len(input_data)):
            data.append(self.getHiddenOutput(input_data[example_num][:-1]))
        iterations = 25
        # initialize an array of arrays containing the loss for each run for each output node
        loss_history = []
        #min_loss_index = 0
        weight_history = []
        for epoch in range(iterations):
            loss = [0.0] * self.out_k
            weights_for_examples = []
            for example_num in range(len(data)):
                if self.uses_regression:
                    predicted = self.output_layer[0].getOutput(data[example_num])
                    error = input_data[example_num][-1] - predicted
                    squared_loss = error * error
                    loss[0] += squared_loss
                    # shallow copy the weights (alias)
                    weights = self.output_layer[0].weights
                    # update weights
                    for weight_num in range(len(weights)):
                        weights[weight_num] = weights[weight_num] + (eta*error*data[example_num][weight_num])

                    weights_for_examples.append(copy.deepcopy(weights))
                else:
                    weights_for_output_node = []
                    for output_num in range(len(self.output_layer)):
                        # positive class is the one held in the one-hot node
                        # negative class is any class not held in the one-hot node
                        prob = self.output_layer[output_num].getOutput(data[example_num])
                        if input_data[example_num][-1] == self.output_layer[output_num].clss:
                            correct = 1
                        else:
                            correct = 0
                        error = correct - prob
                        ## predicted class is positive
                        #if prob > 0.5:
                        #    # true class is negative
                        #    if input_data[example_num][-1] != self.output_layer[output_num].clss:
                        #        error = -2
                        ## predicted class is negative
                        #else:
                        #    # true class is positive
                        #    if input_data[example_num][-1] == self.output_layer[output_num].clss:
                        #        error = 2

                        # shallow copy the weights (alias)
                        weights = self.output_layer[output_num].weights
                        # update weights
                        if error != 0:
                            for weight_num in range(len(weights)):
                                weights[weight_num] = weights[weight_num] + (eta * error * prob * (1.0 - prob) * data[example_num][weight_num])
                        weights_for_output_node = copy.deepcopy(weights)
                        #weights_for_examples.append(copy.deepcopy(weights))
                        #if error != 0:
                        #    error = 1
                        squared_loss = error * error
                        loss[output_num] += squared_loss
                    weights_for_examples.append(weights_for_output_node)
            loss_history.append(loss)
            weight_history.append(weights_for_examples)
            if self.uses_regression:
                print("MSE:", (loss[0] / len(data)))
            else:
                print("MSE per node:", end=' ')
                # print MSE for each output node
                for output_num in range(len(self.output_layer)):
                    print(loss[output_num] / len(data), end=' ')
                print()

    def tune(self, input_data, validation_data):
        print("Tuning RBF Network")
        eta = 0.05
        prev_error = -1
        print("Tuning eta")
        while eta <= 0.5:
            self.trainOutputLayer(input_data, eta, 0)
            error = 0
            if self.uses_regression:
                # get absolute error for each validation observation
                results = ms.testRegressor(self, validation_data)
                for obs in range(len(results)):
                    error += results[obs]
                # convert to MSE
                error = (error * error) / len(validation_data)
            else:
                error = self.testClassification(validation_data)
            print("MSE for eta =",eta,":",error)
            if (prev_error != -1) and (error >= prev_error):
                eta -= 0.05
                for node in range(len(self.output_layer)):
                    self.output_layer[node].resetWeights()
                break
            prev_error = error
            eta += 0.05
            for node in range(len(self.output_layer)):
                self.output_layer[node].resetWeights()
        print("Selected eta =",eta)
        #self.trainOutputLayer(input_data, eta, 0)

        print("Tuning alpha for momentum")
        alpha = 0
        prev_error = -1
        while alpha < 0.5:
            self.trainOutputLayer(input_data, eta, alpha)
            error = 0
            if self.uses_regression:
                # get absolute error for each validation observation
                results = ms.testRegressor(self, validation_data)
                for obs in range(len(results)):
                    error += results[obs]
                # convert to MSE
                error = (error * error) / len(validation_data)
            else:
                error = self.testClassification(validation_data)
            print("MSE for alpha =",alpha,":",error)
            if (prev_error != -1) and (error >= prev_error):
                alpha -= 0.1
                for node in range(len(self.output_layer)):
                    self.output_layer[node].resetWeights()
                break
            prev_error = error
            alpha += 0.1
            for node in range(len(self.output_layer)):
                self.output_layer[node].resetWeights()
        print("Selected alpha =", alpha)


    # predict the value for a new observation
    def predict(self, new_obs):
        if self.uses_regression:
            return self.regress(new_obs)
        else:
            # I have classify return (class, probability) as a tuple for use in tuning, but
            # predict will simply return class
            return self.classify(new_obs)[0]

    def regress(self, new_obs):
        hidden_outputs = self.getHiddenOutput(new_obs)
        return self.output_layer[0].getOutput(hidden_outputs)


    def classify(self, new_obs):
        classes = {}
        for output_num in range(len(self.output_layer)):
            hidden_outputs = self.getHiddenOutput(new_obs)
            classes[self.output_layer[output_num].clss] = self.output_layer[output_num].getOutput(hidden_outputs)
        decision = sorted(classes.items(), key=lambda elem: elem[1], reverse=True)
        return decision[0]


    # will return the MSE for classification
    def testClassification(self, testing_set):
        mse = 0
        for obs in range(len(testing_set)):
            correct_class = testing_set[obs][-1]
            predicted = self.classify(testing_set[obs])
            if predicted[0] == correct_class:
                error = (1 - predicted[1])
            else:
                error = predicted[1]
            mse += error * error
        return mse / len(testing_set)