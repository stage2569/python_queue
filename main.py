import numpy as np


def generate_exponential_times(mean, count):
    """ Generate exponential random variables. """
    return np.random.exponential(mean, count)


class Customer:
    def __init__(self, arrival_time, service_time):
        self.arrival_time = arrival_time
        self.start_service_time = None
        self.service_time = service_time
        self.wait_time = None  # To store the wait time in the queue
        self.assigned_teller = None


class Teller:
    def __init__(self):
        self.queue = []
        self.current_customer = None
        self.idle_time = 0
        self.queue_lengths = []  # List to keep track of queue length over time
        self.customers_served = 0  # Counter for customers served

    def is_idle(self):
        return self.current_customer is None


mean_interarrival_time = 1  # minutes
mean_service_time = 4.5  # minutes
simulation_duration = 8 * 60  # minutes (8 hours)

estimated_customer_count = simulation_duration // mean_interarrival_time
interarrival_times = generate_exponential_times(mean_interarrival_time, estimated_customer_count)
service_times = generate_exponential_times(mean_service_time, estimated_customer_count)

customers = [Customer(arrival, service) for arrival, service in zip(np.cumsum(interarrival_times), service_times)]


def simulate(customers, num_tellers):
    tellers = [Teller() for _ in range(num_tellers)]
    time = 0
    customer_index = 0
    total_customers_queued = 0  # Counter for the total number of customers that enter a queue

    while customer_index < len(customers) or any(not teller.is_idle() for teller in tellers):
        # Check for new customer arrivals
        while customer_index < len(customers) and customers[customer_index].arrival_time <= time:
            # Assign customer to the shortest queue
            shortest_queue = min(tellers, key=lambda t: len(t.queue))
            customers[customer_index].assigned_teller = tellers.index(shortest_queue)
            shortest_queue.queue.append(customers[customer_index])
            total_customers_queued += 1
            customer_index += 1

        # Update tellers and check for jockeying
        for i, teller in enumerate(tellers):
            if teller.is_idle() and teller.queue:
                teller.current_customer = teller.queue.pop(0)
                teller.current_customer.start_service_time = time
                teller.current_customer.wait_time = teller.current_customer.start_service_time - teller.current_customer.arrival_time

                # For debug
                # print(f"Customer starts service at time {time} with wait time {teller.current_customer.wait_time}")

            elif teller.current_customer and time - teller.current_customer.start_service_time >= teller.current_customer.service_time:
                teller.customers_served += 1
                teller.current_customer = None

            # Jockeying logic
            for j, other_teller in enumerate(tellers):
                if other_teller != teller and other_teller.queue and len(other_teller.queue) > len(teller.queue) + 1:
                    jockeying_customer = other_teller.queue.pop(-1)
                    teller.queue.append(jockeying_customer)
                    if teller.is_idle():
                        teller.current_customer = teller.queue.pop(0)
                        teller.current_customer.start_service_time = time
                        teller.current_customer.wait_time = teller.current_customer.start_service_time - teller.current_customer.arrival_time

            # Update idle time and record queue length
            if teller.is_idle():
                teller.idle_time += 1
            teller.queue_lengths.append(len(teller.queue))

        # Increment time
        time += 1

    return tellers, total_customers_queued, customers


def analyze_results(customers, tellers, total_customers_queued):
    total_wait_time = sum(
        (customer.start_service_time - customer.arrival_time) for customer in customers if customer.start_service_time)
    average_wait_time = total_wait_time / len(customers)
    max_wait_time = max(customer.wait_time for customer in customers if customer.wait_time is not None)
    total_idle_time = sum(teller.idle_time for teller in tellers)

    # print(f"Average Wait Time: {average_wait_time:.2f} minutes")
    print(f"Total Idle Time for Tellers: {total_idle_time} minutes")
    print(f"Maximum delay in queue: {max_wait_time:.2f} minutes")

    # Total served & Total queue length
    total_customers_served = sum(teller.customers_served for teller in tellers)
    total_queue_length = sum(sum(teller.queue_lengths) for teller in tellers)

    print(f"Total number of customers served: {total_customers_served}")
    print(f"Total number of customer-minutes spent in queues: {total_queue_length}")

    # Total number in queue
    print(f"Total number of customers that entered a queue: {total_customers_queued}")

    # Average delay
    print(f"Average delay in queue: {average_wait_time:.2f} minutes")


import matplotlib.pyplot as plt
import plotly.graph_objects as go


# Plot Queue Length by Teller
def plot_queue_lengths(tellers):
    num_tellers = len(tellers)
    fig, axes = plt.subplots(num_tellers, 1, figsize=(15, 3 * num_tellers))
    for i, ax in enumerate(axes):
        ax.plot(tellers[i].queue_lengths, label=f'Teller {i + 1}')
        ax.set_title(f'Teller {i + 1}')
        ax.set_xlabel('Time (minutes)')
        ax.set_ylabel('Queue Length')
        ax.grid(True)
    plt.tight_layout()
    plt.show()


# Hist Customer Wait Times
def plot_wait_time_distribution(customers):
    # Extract wait times, ensuring they are not None
    wait_times = [customer.wait_time for customer in customers if customer.wait_time is not None]

    # Check if there are wait times to plot
    if not wait_times:
        print("No wait time data available to plot.")
        return

    plt.figure(figsize=(12, 6))
    plt.hist(wait_times, bins=30, color='skyblue', edgecolor='black')
    plt.xlabel('Wait Time (minutes)')
    plt.ylabel('Number of Customers')
    plt.title('Distribution of Customer Wait Times')
    plt.grid(True)
    plt.show()


# Bar Chart Teller Idle Time
def plot_teller_idle_times(tellers):
    idle_times = [teller.idle_time for teller in tellers]
    plt.figure(figsize=(10, 6))
    plt.bar(range(1, len(tellers) + 1), idle_times, color='lightgreen')
    plt.xlabel('Teller')
    plt.ylabel('Idle Time (minutes)')
    plt.title('Idle Times of Each Teller')
    plt.xticks(range(1, len(tellers) + 1))
    plt.grid(True)
    plt.show()


# Avg Delay in Queue
def plot_average_delay_per_teller(customers, num_tellers):
    average_delays = []
    for i in range(num_tellers):
        teller_customers = [c for c in customers if c.assigned_teller == i and c.wait_time is not None]
        if teller_customers:
            avg_delay = sum(c.wait_time for c in teller_customers) / len(teller_customers)
            average_delays.append(avg_delay)
        else:
            average_delays.append(0)

    plt.figure(figsize=(10, 6))
    plt.bar(range(num_tellers), average_delays, color='lightblue')
    plt.xlabel('Teller')
    plt.ylabel('Average Delay (minutes)')
    plt.title('Average Delay in Queue per Teller')
    plt.xticks(range(num_tellers), [f'Teller {i + 1}' for i in range(num_tellers)])
    plt.grid(True)
    plt.show()


# Maximum delay
def plot_maximum_delay_per_teller(customers, num_tellers):
    max_delays = []
    for i in range(num_tellers):
        teller_customers = [c for c in customers if c.assigned_teller == i and c.wait_time is not None]
        max_delay = max((c.wait_time for c in teller_customers), default=0)
        max_delays.append(max_delay)

    plt.figure(figsize=(10, 6))
    plt.bar(range(num_tellers), max_delays, color='tomato')
    plt.xlabel('Teller')
    plt.ylabel('Maximum Delay (minutes)')
    plt.title('Maximum Delay in Queue per Teller')
    plt.xticks(range(num_tellers), [f'Teller {i + 1}' for i in range(num_tellers)])
    plt.grid(True)
    plt.show()


# Debug
def debug_wait_times(customers):
    wait_times = [customer.wait_time for customer in customers if customer.wait_time is not None]
    print("Sample wait times:", wait_times[:10])  # Print first 10 wait times
    print("Number of customers with recorded wait times:", len(wait_times))


# debug_wait_times(customers)


# Run the simulation
num_tellers = 3  # number of tellers 3,4,5,6,7
tellers, total_customers_queued, customers = simulate(customers, num_tellers)

# Analyze the results
analyze_results(customers, tellers, total_customers_queued)

# Visualize simulation
plot_queue_lengths(tellers)
plot_wait_time_distribution(customers)
plot_teller_idle_times(tellers)
plot_average_delay_per_teller(customers, num_tellers)
plot_maximum_delay_per_teller(customers, num_tellers)