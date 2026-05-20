# Simulación de Smart Meters
## Definicion de como funciona un smart meter
Un smart meter es basicamente un dispositivo que permite hacer lecturas (en este caso de agua) y enviar los datos por ejemplo a un servidor.

Por ejemplo podemos medir el volumen de agua de una tuberia por ejemplo.

Estos contadores no miden todo el chorro, van como trozeando y enviando un aviso al servidor

Para medir esos trozitos, tiene un sensor donde cada trozito es un pulso. El sensor tiene configurado como el minimo, por ejemplo, si tiene configurado 1L, notificara cada vez que note 1L.

## Como funciona el tema de los 3 picos de consumo (Modelo GMM)
Este modelo nos muestra que tiene 3 horas puntas 
- Mañana (Ducha  y desayuno) de ~07:00 a 09:00
- Mediodia (Comida) ~13:30 a 15:00
- Noche (Cena y aseo) ~20:00 a 22:30

En estos picos, habra mucho mas consumo, cuanto mas consumo, mas volumen.

En estas horas, el smart meter enviara mas pulsos al servidor.

### Que es el Modelo GMM

Este es un modelo de mezcla de Gaussianas. 

#### Que es una Gaussiana?
Una gaussiana es basicamente sirve para representar algo que se agrupa alrededor de un punto central pero que tienen un poco de margen de error o retraso.

Pero esta el Modelo GMM muestra **K**, que es el numero de picos que muestra la mezcla.

Estos picos se ocurren a lo largo del dia, por eso se define en horas, donde este valor es el **Eje X**.

La altura de la grafica que es el **Eje Y** es la probabilidad de consumo de esa hora exacta.

El punto donde mas alertas hay, es el punto central ($\mu$), basicamente **la media.**

Cada gaussiana del modelo GMM es independiente de la otra, independientemente de las horas que tenga cada una. Esto es **el peso ($w$)**.

El peso representa el porcentaje total de agua que se gasta en ese pico concreto.
Si se suman los pesos de las K, dara 1, que es el **100% del consumo diario**.

El peso se decide viendo las rutinas que consumen más volumen de agua.

El ancho (Desviacion Estándar $\sigma$) es la dispersion o duracion temporal del pico de consumo. 
Esto quiere decir que puede haber una separacion de alomejor 1h.


Esta desviacion se calcula de la siguiente manera:
1. Calculo de la hora de la ducha, donde hay mas probabilidad que se duche una persona.
   - Se calcula haciendo la media 
2. Medir las diferencias, es cuanto se desvia cada elemento de la media (hora  de la ducha en este caso)
   - Si la media es 8 y una persona se ducha a las 9, hay una desviacion individual de 1h
   - Si otra persona se ducha a las 7, la desviacion de -1h.
3. Estas medidas se elevan al cuadrado ($desviacion\_individual^2$) para que no de numeros negativos. Luego se hace la media de estos valores, donde calculamos la **varianza**
4. Por ultimo se desconvierte el 'horas al cuadrado' para que sean horas reales, haciendo una raiz cuadrada

Todo esto es para saber cuanto se desvia los consumos de la hora central.

| ! Se usa elevado al cuadrado para que tenga mas peso los outliers.

## Ecuación de la Demanda Teórica
$$P(t) = \sum_{k=1}^{K} w_k \cdot \mathcal{N}(t; \mu_k, \sigma_k^2)$$

La funcion de densidad de probabilidad (PDF) es la que nos junta las 3 Gaussianas que define la probabilidad que haya consumo en una hora

la K son las 3 fases que teneos (gaussianas) que son Mañana|Mediodia|Noche

$P(t)$ es lo que queremos averiguar. Que es la probabilidad de consumo en una hora en concreto, donde t representa la hora ([0,24])

$\sum_{k=1}^{K}$ nos indica que mezcla las K (K = 3) y las suma

$w_k$ es el peso que define la probabilidad del consumo de % (0, 24) de una K

$\mathcal{N}(t; \mu_k, \sigma_k^2)$ es la funcion matematica de la campana de gauss para un momento (t).  Donde recibe:
    
- $t$ que es la hora
- $\mu_k$ que es la media (hora central) de una K
- La varianza de una K

## Inclusión de perdidas por fuga (Ruido Base)
$$P_{\text{total}}(t) = P(t) \cdot I_{\text{familiar}} + P_{\text{base}}$$

Esto nos permite simular fugas o consumo minimo residual nocturno.

Se usa ${I_\text{familiar}}$ que es un multiplicador aleatorio asignado a cada hogar para poder simular familias numerosas (alto consumo) o personas solas (bajo consumo).
Este valor nos permite hacer cuanto se desvia un consumo de una casa del consumo estandar


${P_\text{base}}$ que es una probabilidad basal constante, un porcentaje, por ejemplo 0.02 (2%)

# Probabilidad continua al Tick de Simulación (Proceso de Bernoulli)
El proceso de Bernoulli es cualquier accion o evento que tiene dos resultados posibles (0,1)
Por ejemplo cuando tiras 10 veces una moneda en el tiempo, se crea una secuencia de 0, 1, eso es el proceso de bernoulli.

Cada vez que pasa un litro de agua por el sensor, emite un pulso o señal digital (evento) aqui sera un 1 por pulos, donde dice, ¡ha pasado 1 litro!

Para ello primero se sigue este flujo:
1. Se define un paso del tiempo ($\Delta t$) que es la frecuencia del servidor en hacerle la peticion al contador. Si se decide mirar 1 minuto el contado, cada minuto hara una peticion.
2. Evaluamos la probabilidad continua en el instante (h) actual ($P_{\text{total}}(t)$) donde llama a la ecuacion de la Probabilidad Total
3. Calculamos la siguiente ecuacion porque nosotros hacemos peticiones segun el paso del tiempo, en este caso minutos, y el P_total devuelve para horas
$$P_{\text{tick}} = P_{\text{total}}(t) \cdot \Delta t$$
1. Usamos un numero pseudoaleatorio  ($r$) uniforme y si ($r < P_{\text{tick}}$), es que ha pasado 1 litro de agua y lanza evento, si no no lanza

## Desincronización de contadores
En los contadores, cada contador emiten pulsos distintos, no se coordinan y hacen uno en un microsegundo, entonces aqui aplicamos varias cosas:
1. se asigna un numero aleatorio entre $-45$ y $+45$ minutos para que se desplaze y asigne los habitos del hogar para que unos madrugen antes o que cenen mas tarde.
2. Intensidad de consumo ($I_{\text{familiar}}$) Nos permite aumemntar o reducir la probabilidad  de generar pulsos, haciendo familias numerosas o de una persona