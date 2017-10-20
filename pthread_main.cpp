#include <bits/stdc++.h>
#include <pthread.h>
#include <sys/time.h>

using namespace std;

#define MAXN 10000000
#define THREAD_NUM 4

struct param_t{
	int l, r;
	int * D, * A;
};

class Core {

public:

	Core() { N = -1; D = NULL; }

	void preprocess(int n) {
		if (n<=0||D!=NULL) return;
		N = n;
		D = generate(n);
	}

	void release() {
		free(D);
		D = NULL;
	}

	int query(int l, int r) {
		int len = r - l + 1;
		int dlen = len / THREAD_NUM;
		for (int i=0;i<THREAD_NUM;++i) {
			params_[i].l = i*dlen + l;
			params_[i].r = params_[i].l + dlen;
			if (i+1 == THREAD_NUM) params_[i].r+=len%THREAD_NUM;
			params_[i].D = D;
			params_[i].A = (int*)ans[i];
			pthread_create(threads_+i, NULL, run_func, params_+i);
		}
		int ret = 0;
		for (int i=0;i<THREAD_NUM;++i) {
			pthread_join(threads_[i], NULL);
			ret = max(ret, *(params_[i].A));
		}
		return ret;
	}

private:

	int N;
	int * D;
	pthread_t threads_[THREAD_NUM];
	param_t params_[THREAD_NUM];
	int ans[THREAD_NUM][8];

	int * generate(int n) {
		int * d = (int *)malloc(sizeof(int)*n);
		for (int i=0;i<n;++i) d[i] = rand()%100000000;
		return d;
	}

	static void * run_func(void * args) {
		int ret = 0;
		param_t * p = (param_t *)args;
		for (int i=p->l;i<p->r;++i) {
			ret = max(ret, (p->D)[i]);
		}
		(p->A)[0] = ret;
	}

};

unsigned long cur_time() {
	struct timeval current;
	gettimeofday(&current, NULL);
	auto currentTime = current.tv_sec * 1000 + current.tv_usec/1000;
	return currentTime;
}

int main() {

	Core * q = new Core();

	q->preprocess(MAXN);

	int st = time(0);

	for (int i=0;i<1000;++i) {
		int l = rand()%1000000;
		int r = l + rand()%8000000;
		int ans = q->query(l, r);
		// cout<<ans<<endl;
	}

	int en = time(0);

	cout<< en - st <<endl;

	q->release();
	free(q);

	return 0;
}
