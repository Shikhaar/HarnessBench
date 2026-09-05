package cache

type Cache struct {
	items map[string]interface{}
}

func NewCache() *Cache {
	return &Cache{
		items: make(map[string]interface{}),
	}
}

func (c *Cache) Get(key string) (interface{}, bool) {
	// BUG: Unprotected map read triggers concurrent map read/write race
	val, ok := c.items[key]
	return val, ok
}

func (c *Cache) Set(key string, val interface{}) {
	// BUG: Unprotected map write triggers data race
	c.items[key] = val
}
