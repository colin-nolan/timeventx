const JSON_CONTENT_TYPE_HEADER = {
    "Content-Type": "application/json",
};

export type TimerId = number;
export type Second = number;

export interface Timer {
    id?: TimerId;
    name: string;
    startTime: string;
    duration: Second;
}

export interface Interval {
    startTime: string;
    endTime: string;
}

export class ApiClient {
    apiRootUrl: string;
    timers: TimersClient;

    constructor(apiRootUrl: string) {
        this.apiRootUrl = apiRootUrl;
        this.timers = new TimersClient(apiRootUrl);
    }

    getStats(): Promise<string> {
        return new Promise<string>((resolve, reject) => {
            wrappedFetch("getting stats", `${this.apiRootUrl}/stats`)
                .then(async (response) => {
                    const stats = await response.text();
                    resolve(stats);
                })
                .catch((error) => {
                    reject(error);
                });
        });
    }

    getLogs(): Promise<string> {
        return new Promise<string>((resolve, reject) => {
            wrappedFetch("getting logs", `${this.apiRootUrl}/logs`)
                .then(async (response) => {
                    const logs = await response.text();
                    resolve(logs);
                })
                .catch((error) => {
                    reject(error);
                });
        });
    }

    getConfig(): Promise<object> {
        return new Promise<object>((resolve, reject) => {
            wrappedFetch("getting config", `${this.apiRootUrl}/config`)
                .then(async (response) => {
                    const config = await response.json();
                    resolve(config);
                })
                .catch((error) => {
                    reject(error);
                });
        });
    }

    clearLogs(): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            wrappedFetch("clearing logs", `${this.apiRootUrl}/logs`, { method: "DELETE" })
                .then(async (response) => {
                    resolve();
                })
                .catch((error) => {
                    reject(error);
                });
        });
    }

    resetDevice(): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            wrappedFetch("resetting device", `${this.apiRootUrl}/reset`, { method: "POST" })
                .then(async (response) => {
                    let online = false;
                    while (!online) {
                        try {
                            const response = await fetch(`${this.apiRootUrl}/healthcheck`);
                            if (response.ok) {
                                online = true;
                            }
                        } catch (error) {
                            await new Promise((resolve) => setTimeout(resolve, 250));
                        }
                    }
                    resolve();
                })
                .catch((error) => {
                    reject(error);
                });
        });
    }

    getIntervals(): Promise<Interval[]> {
        return new Promise<Interval[]>((resolve, reject) => {
            wrappedFetch("get intervals", `${this.apiRootUrl}/intervals`)
                .then(async (response) => {
                    const intervals = await response.json();
                    resolve(intervals);
                })
                .catch((error) => {
                    reject(error);
                });
        });
    }
}

export class TimersClient {
    apiRootUrl: string;

    constructor(apiRootUrl: string) {
        this.apiRootUrl = apiRootUrl;
    }

    addOrUpdateTimer(timer: Timer): Promise<Timer> {
        return timer.id ? this.updateTimer(timer) : this.addTimer(timer);
    }

    addTimer(timer: Timer): Promise<Timer> {
        return new Promise<Timer>((resolve, reject) => {
            wrappedFetch("adding timer", `${this.apiRootUrl}/timer`, {
                method: "POST",
                headers: JSON_CONTENT_TYPE_HEADER,
                body: JSON.stringify(timer),
            })
                .then(async (response) => {
                    const addedTimer = await response.json();
                    resolve(addedTimer);
                })
                .catch((error) => {
                    reject(error);
                });
        });
    }

    updateTimer(timer: Timer): Promise<Timer> {
        return new Promise<Timer>((resolve, reject) => {
            wrappedFetch("updating timer", `${this.apiRootUrl}/timer/${timer.id}`, {
                method: "PUT",
                headers: JSON_CONTENT_TYPE_HEADER,
                body: JSON.stringify(timer),
            })
                .then(async (response) => {
                    const updatedTimer = await response.json();
                    resolve(updatedTimer);
                })
                .catch((error) => {
                    reject(error);
                });
        });
    }

    removeTimer(timerId: TimerId): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            wrappedFetch("removing timer", `${this.apiRootUrl}/timer/${timerId}`, {
                method: "DELETE",
                headers: JSON_CONTENT_TYPE_HEADER,
            })
                .then(async (response) => {
                    resolve();
                })
                .catch((error) => {
                    reject(error);
                });
        });
    }

    getTimers(): Promise<Timer[]> {
        return new Promise<Timer[]>((resolve, reject) => {
            wrappedFetch("fetching timers", `${this.apiRootUrl}/timers`)
                .then(async (response) => {
                    const timers = await response.json();
                    resolve(timers);
                })
                .catch((error) => {
                    reject(error);
                });
        });
    }
}

function wrappedFetch(action: string, url: string, options?: RequestInit): Promise<Response> {
    options = options || {};
    return new Promise<Response>((resolve, reject) => {
        fetch(url, options)
            .then(async (response) => {
                if (!response.ok) {
                    const reason = await response.text();
                    console.error(response);
                    reject(`Problem ${action}: ${reason}`);
                }
                resolve(response);
            })
            .catch((error) => {
                console.error(error);
                reject(`Error ${action}: ${error}`);
            });
    });
}
