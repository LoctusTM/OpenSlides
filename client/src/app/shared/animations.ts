import { trigger, animate, transition, style, query, stagger, group } from '@angular/animations';

export const pageTransition = trigger('pageTransition', [
    transition('* => *', [
        /** this will avoid the dom-copy-effect */
        query(':enter, :leave', style({ position: 'absolute', width: '100%' }), { optional: true }),
        /** keep the dom clean - let all items "just" enter */
        query(':enter mat-card', [style({ opacity: 0 })], { optional: true }),
        query(':enter .on-transition-fade', [style({ opacity: 0 })], { optional: true }),
        query(':enter mat-row', [style({ opacity: 0 })], { optional: true }),
        query(':enter mat-expansion-panel', [style({ opacity: 0 })], { optional: true }),

        /** parallel vanishing */
        group([
            /** animate fade out for the selected components */
            query(
                ':leave .on-transition-fade',
                [
                    style({ opacity: 1 }),
                    animate(
                        '200ms ease-in-out',
                        style({
                            transform: 'translateY(0%)',
                            opacity: 0
                        })
                    )
                ],
                { optional: true }
            ),
            /** how the material cards are leaving */
            query(
                ':leave mat-card',
                [
                    style({ transform: 'translateY(0%)', opacity: 1 }),
                    animate(
                        '200ms ease-in-out',
                        style({
                            transform: 'translateY(0%)',
                            opacity: 0
                        })
                    )
                ],
                { optional: true }
            ),
            query(
                ':leave mat-row',
                [
                    style({ transform: 'translateY(0%)', opacity: 1 }),
                    animate(
                        '200ms ease-in-out',
                        style({
                            transform: 'translateY(0%)',
                            opacity: 0
                        })
                    )
                ],
                { optional: true }
            ),
            query(
                ':leave mat-expansion-panel',
                [
                    style({ transform: 'translateY(0%)', opacity: 1 }),
                    animate(
                        '200ms ease-in-out',
                        style({
                            transform: 'translateY(0%)',
                            opacity: 0
                        })
                    )
                ],
                { optional: true }
            )
        ]),

        /** parallel appearing */
        group([
            /** animate fade in for the selected components */
            query(':enter .on-transition-fade', [style({ opacity: 0 }), animate('0.2s', style({ opacity: 1 }))], {
                optional: true
            }),
            /** how the mat cards enters the scene */
            query(
                ':enter mat-card',
                /** stagger = "one after another" with a distance of 50ms" */
                stagger(50, [
                    style({ transform: 'translateY(50px)' }),
                    animate('300ms ease-in-out', style({ transform: 'translateY(0px)', opacity: 1 }))
                ]),
                { optional: true }
            ),
            query(
                ':enter mat-row',
                /** stagger = "one after another" with a distance of 50ms" */
                stagger(30, [
                    style({ transform: 'translateY(24px)' }),
                    animate('200ms ease-in-out', style({ transform: 'translateY(0px)', opacity: 1 }))
                ]),
                { optional: true }
            ),
            query(
                ':enter mat-expansion-panel',
                /** stagger = "one after another" with a distance of 50ms" */
                stagger(100, [
                    style({ transform: 'translateY(50px)' }),
                    animate('300ms ease-in-out', style({ transform: 'translateY(0px)', opacity: 1 }))
                ]),
                { optional: true }
            )
        ])
    ])
]);

export const navItemAnim = trigger('navItemAnim', [
    transition(':enter', [style({ transform: 'translateX(-100%)' }), animate('500ms ease')]),
    transition(':leave', [style({ transform: 'translateX(100%)' }), animate('500ms ease')])
]);
